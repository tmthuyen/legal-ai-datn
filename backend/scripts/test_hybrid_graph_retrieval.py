"""
test_hybrid_graph_retrieval.py
Kiểm tra hợp đồng của luồng Hybrid Search + Graph Traverse mà không cần Neo4j.

Script dùng graph service và hybrid searcher giả lập để xác nhận:
- Kết quả có đúng 3 key: input, relevant_laws, relevant_documents.
- Mỗi law node có `relationships` lồng nhau với hướng OUTGOING/INCOMING hợp lệ.
- Quan hệ CONTAINS tới tổ tiên là INCOMING, tới hậu duệ là OUTGOING.
- Payload parse được bằng `HybridGraphResult`.

Chạy (từ thư mục `backend/`):
    python scripts/test_hybrid_graph_retrieval.py
"""

import sys
from typing import Any

from src.api.api_schemas import HybridGraphResult
from src.retrieval.graph_traverse import GraphTraverse
from src.retrieval.retrieval_service import RetrievalService

DOC = {
    "node_id": "BLDS_2015",
    "label": "Document",
    "document_id": "BLDS_2015",
    "title": "Bộ luật Dân sự 2015",
}
CHAPTER = {
    "node_id": "BLDS_2015_P5_CH20",
    "label": "Chapter",
    "document_id": "BLDS_2015",
    "parent_id": "BLDS_2015",
}
ARTICLE = {
    "node_id": "BLDS_2015_D688",
    "label": "Article",
    "document_id": "BLDS_2015",
    "parent_id": "BLDS_2015_P5_CH20",
    "full_text": "Nội dung Điều 688.",
}
CLAUSE = {
    "node_id": "BLDS_2015_D688_K1",
    "label": "Clause",
    "document_id": "BLDS_2015",
    "parent_id": "BLDS_2015_D688",
    "text": "Nội dung Khoản 1.",
}
POINT = {
    "node_id": "BLDS_2015_D688_K1_DIEM_A",
    "label": "Point",
    "document_id": "BLDS_2015",
    "parent_id": "BLDS_2015_D688_K1",
}
RELATED_ARTICLE = {
    "node_id": "BLDS_2015_D125",
    "label": "Article",
    "document_id": "BLDS_2015",
    "parent_id": "BLDS_2015_P1_CH3",
}


class StubGraphService:
    """Giả lập LegalGraphService với một cây phân cấp nhỏ."""

    def get_breadcrumbs(self, node_id: str) -> list[dict[str, Any]]:
        """Trả về tổ tiên cố định của Điều 688."""
        return [DOC, CHAPTER, ARTICLE]

    def get_descendants(
        self, node_id: str, max_depth: int = 5, limit: int = 200
    ) -> list[dict[str, Any]]:
        """Trả về hậu duệ cố định của Điều 688."""
        return [CLAUSE, POINT]

    def get_related_laws(self, node_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Trả về một CONTAINS (bị lọc) và hai quan hệ pháp lý."""
        return [
            {
                "relation_type": "CONTAINS",
                "direction": "OUTGOING",
                "target_node": CLAUSE,
            },
            {
                "relation_type": "REFERENCES",
                "direction": "OUTGOING",
                "target_node": RELATED_ARTICLE,
            },
            {
                "relation_type": "IMPLEMENTS",
                "direction": "INCOMING",
                "source_node": RELATED_ARTICLE,
            },
        ]

    def get_citation_path(self, node_id: str) -> str:
        """Trả về trích dẫn giả lập theo node_id."""
        return f"citation:{node_id}"

    def get_node_by_id(self, node_id: str) -> dict[str, Any] | None:
        """Trả về Document hoặc node liên quan theo node_id."""
        return {
            "BLDS_2015": DOC,
            "BLDS_2015_D125": RELATED_ARTICLE,
        }.get(node_id)


class EmptyHybridSearcher:
    """Giả lập HybridSearcher không tìm thấy seed node."""

    def search(self, query: str, top_k: int = 5) -> dict[str, Any]:
        """Trả về danh sách rỗng."""
        return {"results": []}


class StubHybridSearcher:
    """Giả lập HybridSearcher trả về hai seed node."""

    def search(self, query: str, top_k: int = 5) -> dict[str, Any]:
        """Trả về danh sách seed cố định kèm metadata xếp hạng."""
        return {
            "results": [
                {
                    **ARTICLE,
                    "score": 0.032,
                    "rrf_score": 0.032,
                    "rank": 1,
                    "semantic_rank": 1,
                    "bm25_rank": 2,
                    "retrieval_source": "hybrid[semantic+bm25]",
                },
                {
                    **RELATED_ARTICLE,
                    "score": 0.016,
                    "rrf_score": 0.016,
                    "rank": 2,
                    "semantic_rank": 3,
                    "bm25_rank": None,
                    "retrieval_source": "hybrid[semantic_only]",
                },
            ]
        }


def main() -> None:
    """Chạy kiểm tra hợp đồng và in kết quả tóm tắt."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    service = RetrievalService(
        legal_query_extractor=None,
        legal_graph_service=StubGraphService(),
        semantic_service=StubHybridSearcher(),
        hybrid_service=StubHybridSearcher(),
        graph_traverse=GraphTraverse(StubGraphService()),
    )

    result = service.retrieve_hybrid_and_graph("thừa kế theo pháp luật", top_k=2)

    assert sorted(result) == ["input", "relevant_documents", "relevant_laws"]

    laws = result["relevant_laws"]
    assert len(laws) == 2

    first_relationships = laws[0]["relationships"]
    directions = {
        (item["relation_type"], item["direction"]) for item in first_relationships
    }
    assert ("CONTAINS", "INCOMING") in directions, "thiếu cạnh CONTAINS tới tổ tiên"
    assert ("CONTAINS", "OUTGOING") in directions, "thiếu cạnh CONTAINS tới hậu duệ"
    assert ("REFERENCES", "OUTGOING") in directions, "thiếu cạnh REFERENCES"
    assert all(
        item["relation_type"] != "CONTAINS"
        or item["related_node"]["label"] != "Document"
        for item in first_relationships
    ), "Document không được xuất hiện trong quan hệ phân cấp"

    assert [doc["node_id"] for doc in result["relevant_documents"]] == ["BLDS_2015"]

    typed = HybridGraphResult(**result)
    assert typed.relevant_laws[0].node_id == "BLDS_2015_D688"
    assert len(typed.relevant_laws[0].relationships) == len(first_relationships)

    empty_service = RetrievalService(
        legal_query_extractor=None,
        legal_graph_service=StubGraphService(),
        semantic_service=EmptyHybridSearcher(),
        hybrid_service=EmptyHybridSearcher(),
        graph_traverse=GraphTraverse(StubGraphService()),
    )
    empty = empty_service.retrieve_hybrid_and_graph("câu hỏi không khớp", top_k=2)
    assert empty == {
        "input": "câu hỏi không khớp",
        "relevant_laws": [],
        "relevant_documents": [],
    }

    print("Hybrid + Graph contract: OK")
    print(f"  law nodes          : {len(laws)}")
    print(f"  relationships[0]   : {len(first_relationships)}")
    print(f"  directions[0]      : {sorted(directions)}")
    print(
        f"  documents          : {[d['node_id'] for d in result['relevant_documents']]}"
    )


if __name__ == "__main__":
    main()
