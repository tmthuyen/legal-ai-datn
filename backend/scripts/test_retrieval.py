"""
test_retrieval.py
Script chạy thủ công pipeline Retrieval V1: Parse -> Validate -> Resolve -> Graph Retrieval.

Luồng xử lý:
  1. Parse câu hỏi -> `LegalHierarchy` (LegalQueryExtractor - regex baseline).
  2. G1: `LegalHierarchy.validate` kiểm tra hình dạng phân cấp.
  3. `DocumentResolver`: tên văn bản trong câu hỏi -> `document_id`
     (đọc aliases + metadata trong `data/documents_config.json`).
  4. G2: `LegalGraphService.resolve_target_node` -> node đích trên đồ thị.
  5. Gom ngữ cảnh (chỉ node chạm được): cha (breadcrumbs) + con (children)
     + con cháu (descendants) + quan hệ pháp lý + provenance tài liệu.
  6. Format output 6 key + `citation` tuyệt đối cho mọi node.

Nguyên tắc:
  - Node type là **label** lưu trong graph (không đọc property `type`).
  - Không chạm được node -> `SemanticSearchTemp` (stub V1), KHÔNG bịa đặt thông tin luật.
  - Kết quả trả về luôn là **list**, khử trùng theo id, giữ nguyên toàn bộ field gốc.

Chạy (từ thư mục `backend/`):
    python scripts/test_retrieval.py
"""

import json
import sys
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

from src.common.schemas import LegalHierarchy
from src.graph.graph_repository import LegalGraphRepository
from src.graph.graph_service import LegalGraphService
from src.graph.neo4j_client import Neo4jClient
from src.retrieval.legal_query_extractor import LegalQueryExtractor
from src.utils.logger import setup_logger

# ---------------------------------------------------------------------------
# Đường dẫn & môi trường
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
DOCUMENTS_CONFIG_PATH = DATA_DIR / "documents_config.json"

load_dotenv(BACKEND_DIR / ".env")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logger = setup_logger("test_retrieval", "test_retrieval.log")

# Các nhãn node pháp lý có thật trên đồ thị.
NODE_TYPE_LABELS = {
    "Document",
    "Part",
    "Chapter",
    "Section",
    "SubSection",
    "Article",
    "Clause",
    "Point",
}


def format_node(node: dict[str, Any], service: LegalGraphService) -> dict[str, Any]:
    """Giữ nguyên toàn bộ field gốc của node và bổ sung `citation` tuyệt đối.

    Args:
        node: Dict node đọc từ graph.
        service: Service dùng để trích xuất `citation` tuyệt đối.

    Returns:
        Dict gồm toàn bộ field gốc của node + `citation`.
    """
    node_id = node.get("node_id")
    return {
        **node,
        "citation": service.get_citation_path(node_id),
    }


# ---------------------------------------------------------------------------
# Semantic search (stub V1)
# ---------------------------------------------------------------------------
class SemanticSearchTemp:
    """Bản cài tạm (stub) cho semantic search V1: giữ đúng chữ ký, trả rỗng.

    Sẽ được thay bằng semantic search thật (Neo4j vector index) ở V2.
    """

    @staticmethod
    def search(
        query_text: str,
        label: str = "Document",
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Tìm kiếm ngữ nghĩa theo text + label (mặc định `Document`).

        Args:
            query_text: Câu hỏi gốc.
            label: Loại node cần tìm (label graph).
            top_k: Số node tối đa trả về.

        Returns:
            list[dict]: Danh sách node khớp nhất (toàn bộ field gốc + `score`).
        """
        return [
            {
                "verification_scope": "effective_from only; status and effective_to are unverified legacy values",
                "label": "Document",
                "document_id": "BLDS_2015",
                "title": "Bộ luật Dân sự 2015",
                "issuer": "Quốc hội",
                "source_file": "bo_luat_dan_su_91-2015-QH13.docx",
                "number": "91/2015/QH13",
                "metadata_source": "DOCX nguồn: van_ban/bo_luat_dan_su_91-2015-QH13.docx; effective_from: Điều 689",
                "verified_at": "2026-10-07",
                "effective_from": "2017-01-01",
                "node_id": "BLDS_2015",
                "document_type": "BO_LUAT",
                "status": "CON_HIEU_LUC",
                "labels": ["LegalNode", "Document"],
            },
            {
                "verification_scope": "effective_from verified via NQ 64/2013/QH13 (ItemID 32804); status verified via CSDL Quốc gia VBPL ItemID 32801 (sửa đổi bởi NQ 203/2025/QH15)",
                "status_verified_at": "2026-10-07",
                "label": "Document",
                "document_id": "HIEN_PHAP_2013",
                "title": "Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013",
                "issuer": "Quốc hội",
                "source_file": "Hien_phap_nam_2013.docx",
                "source_url": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=32801",
                "number": "Không số",
                "metadata_source": "DOCX nguồn: van_ban/Hien_phap_nam_2013.docx; effective_from: Nghị quyết 64/2013/QH13, Điều 1; status: CSDL Quốc gia VBPL ItemID 32801 (sửa đổi bởi Nghị quyết 203/2025/QH15)",
                "effective_from_source_url": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=32804",
                "verified_at": "2026-10-07",
                "effective_from": "2014-01-01",
                "node_id": "HIEN_PHAP_2013",
                "document_type": "HIEN_PHAP",
                "status": "HET_HIEU_LUC_MOT_PHAN",
                "labels": ["LegalNode", "Document"],
            },
        ]

    @staticmethod
    def search_all_graph(
        query_text: str,
        top_k: int = 10,
    ) -> dict[str, dict[str, list[dict[str, Any]]]]:
        """Tìm kiếm ngữ nghĩa toàn graph, trả top `top_k` node/document.

        Args:
            query_text: Câu hỏi gốc.
            top_k: Số node tối đa cho mỗi nhóm kết quả.

        Returns:
            dict: `{"results": {"related_nodes": [...], "related_documents": [...]}}`,
            mỗi list là top `top_k` đã khử trùng. Stub V1 trả list rỗng.
        """
        return {
            "results": {
                "related_nodes": [],
                "related_documents": [
                    {
                        "verification_scope": "effective_from only; status and effective_to are unverified legacy values",
                        "label": "Document",
                        "document_id": "BLDS_2015",
                        "title": "Bộ luật Dân sự 2015",
                        "issuer": "Quốc hội",
                        "source_file": "bo_luat_dan_su_91-2015-QH13.docx",
                        "number": "91/2015/QH13",
                        "metadata_source": "DOCX nguồn: van_ban/bo_luat_dan_su_91-2015-QH13.docx; effective_from: Điều 689",
                        "verified_at": "2026-10-07",
                        "effective_from": "2017-01-01",
                        "node_id": "BLDS_2015",
                        "document_type": "BO_LUAT",
                        "status": "CON_HIEU_LUC",
                        "labels": ["LegalNode", "Document"],
                    },
                    {
                        "verification_scope": "effective_from verified via NQ 64/2013/QH13 (ItemID 32804); status verified via CSDL Quốc gia VBPL ItemID 32801 (sửa đổi bởi NQ 203/2025/QH15)",
                        "status_verified_at": "2026-10-07",
                        "label": "Document",
                        "document_id": "HIEN_PHAP_2013",
                        "title": "Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013",
                        "issuer": "Quốc hội",
                        "source_file": "Hien_phap_nam_2013.docx",
                        "source_url": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=32801",
                        "number": "Không số",
                        "metadata_source": "DOCX nguồn: van_ban/Hien_phap_nam_2013.docx; effective_from: Nghị quyết 64/2013/QH13, Điều 1; status: CSDL Quốc gia VBPL ItemID 32801 (sửa đổi bởi Nghị quyết 203/2025/QH15)",
                        "effective_from_source_url": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=32804",
                        "verified_at": "2026-10-07",
                        "effective_from": "2014-01-01",
                        "node_id": "HIEN_PHAP_2013",
                        "document_type": "HIEN_PHAP",
                        "status": "HET_HIEU_LUC_MOT_PHAN",
                        "labels": ["LegalNode", "Document"],
                    },
                ],
            }
        }


# ---------------------------------------------------------------------------
# Orchestrator V1
# ---------------------------------------------------------------------------
class RetrievalOrchestrator:
    """Điều phối pipeline Retrieval V1 và dựng output 6 key theo đặc tả."""

    def __init__(
        self,
        service: LegalGraphService,
        extractor: LegalQueryExtractor,
    ):
        """Khởi tạo orchestrator.

        Args:
            service: Service truy vấn đồ thị.
            extractor: Bộ parse câu hỏi -> phân cấp.
        """
        self._service = service
        self._extractor = extractor

    def format_node(self, node: dict[str, Any]) -> dict[str, Any]:
        """Giữ nguyên toàn bộ field gốc của node và bổ sung `citation` tuyệt đối.

        Args:
            node: Dict node đọc từ graph.
            service: Service dùng để trích xuất `citation` tuyệt đối.

        Returns:
            Dict gồm toàn bộ field gốc của node + `citation`.
        """
        node_id = node.get("node_id")
        return {
            **node,
            "citation": self._service.get_citation_path(node_id),
        }

    def retrieve(
        self, query_text: str, document_hint: Optional[str] = None
    ) -> dict[str, Any]:
        """Chạy pipeline Retrieval V1 cho một câu hỏi.

        Args:
            query_text: Câu hỏi người dùng (có trích dẫn vị trí luật).
            document_hint: Tên văn bản gợi ý (nếu có).

        Returns:
            Dict output 6 key: input, extracted_hierarchy, node_information (target node nếu có),
            related_documents, related_nodes, relationships.
        """

        # Khử trùng theo id (dict giữ thứ tự chèn, tránh lỗi set không chứa được dict).
        related_documents: dict[str, dict[str, Any]] = {}
        related_nodes: dict[str, dict[str, Any]] = {}
        related_relationships: list[tuple[str, dict[str, Any]]] = []

        # văn bản hard code để test (vì chưa có model trích xuất document_name từ câu hỏi)
        defalt_document = "Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013"

        # (1) Parse cấu trúc từ câu hỏi.
        extracted = self._extractor.extract_hierarchy(
            query_text=query_text, document=defalt_document
        )
        # Dùng khi có model tự trích xuất
        # extracted = self._extractor.extract_hierarchy_with_model(
        #     query_text=query_text
        # )

        has_hierarchy = extracted.get("has_hierarchy", False)
        valid_hierarchy = extracted.get("valid_hierarchy", False)
        hierarchy_dict = extracted.get("hierarchy", {})
        hierarchy = LegalHierarchy.from_dict(hierarchy_dict)

        # Nếu có cấu trúc phân cấp thì search theo phân cấp,
        if has_hierarchy:
            # Phân cấp không hợp lệ thì return và lỗi
            if not valid_hierarchy:
                logger.error(
                    f"Phân cấp parse được từ câu hỏi không hợp lệ: {hierarchy.to_dict()}"
                )

                return {
                    "input": query_text,
                    "extracted_hierarchy": hierarchy_dict,
                    "node_information": None,
                    "related_documents": [],
                    "related_nodes": [],
                    "relationships": [],
                }

            # Tìm kiếm theo document name với semantic để lấy top document liên quan
            semantic_search_documents = SemanticSearchTemp.search(
                query_text=query_text,
                label="Document",
                top_k=5,
            )
            # Duyệt các doc vừa tìm để tạo node
            for doc in semantic_search_documents:
                document_id = doc.get("document_id") or doc.get("node_id")
                if document_id is None:
                    continue

                document_name = doc.get("title")
                logger.info(
                    f"Document resolved: {document_name} (document_id: {document_id})"
                )

                node_id = hierarchy.get_node_id_from_document_id(
                    document_id=document_id
                )
                logger.info(
                    f"Node ID resolved from document_id {document_id}: {node_id}"
                )

                # tìm kiếm node trên graph
                # Không có thì loại bỏ,
                node = self._service.get_node_by_id(node_id)
                if node is None:
                    logger.warning(f"Node not found for node_id {node_id}")
                    continue

                # tìm các node con, cháu và thêm vào tập kết quả (khử trùng theo node_id)
                related_nodes[node_id] = node
                seed_ids = [node_id]

                # gom các node liên quan (cha, con, con cháu) và quan hệ pháp lý
                nodes = self._collect_related_nodes(seed_ids)
                for n in nodes:
                    related_nodes[n["node_id"]] = n

                # related relationships
                legal_relationships = self._collect_legal_relationships(seed_ids)
                related_relationships.extend(legal_relationships)

                related_documents[document_id] = doc

            # Nếu không có node và document nào được tìm thấy, return
            if not related_nodes and not related_documents:
                logger.warning(
                    "No related nodes or documents found from semantic search."
                )
                return {
                    "input": query_text,
                    "extracted_hierarchy": hierarchy_dict,
                    "node_information": None,
                    "related_documents": [],
                    "related_nodes": [],
                    "relationships": [],
                }

            # lọc các node liên quan nhất với query_text bằng semantic search, giảm số lượng node cần xử lý bước sau
            related_node_list = list(related_nodes.values())
            logger.info(
                f"Total related nodes before semantic filtering: {len(related_node_list)}"
            )
            for node in related_node_list:
                score = 1.0  # Kết quả SEMANTIC SEARCH
                logger.info(f"Node {node.get('node_id')} has semantic score: {score}")

                # Nếu thấp thì loai bỏ node khỏi tập kết quả
                if score < 0.5:
                    related_nodes.pop(node.get("node_id"), None)
                    logger.info(
                        f"Node {node.get('node_id')} removed due to low semantic score."
                    )

            logger.info(
                f"Total related nodes after semantic filtering: {len(related_nodes)}"
            )

            # Lọc document chính xác của node, không loại doc liên quan
            top_score = 0
            for doc in semantic_search_documents:
                score = doc.get("score", 0)
                if score > top_score:
                    top_score = score
                    hierarchy.document = doc.get("title")

            return {
                "input": query_text,
                "extracted_hierarchy": hierarchy_dict,
                "node_information": hierarchy.get_all_info() if hierarchy else None,
                "related_documents": [
                    self.format_node(doc) for doc in related_documents.values()
                ],
                "related_nodes": [
                    self.format_node(node) for node in related_nodes.values()
                ],
                "relationships": self._build_relationships(
                    list(related_nodes.values()), related_relationships
                ),
            }

        # Nếu không có phân cấp: semantic search (V2) hoặc fallback search (V1) để tìm node liên quan.
        # Tìm kiếm toàn graph theo semantic search
        semantic_search_nodes = SemanticSearchTemp.search_all_graph(
            query_text=query_text,
            top_k=10,
        )
        results = semantic_search_nodes.get("results", {})
        related_nodes_semantic = results.get("related_nodes", [])
        related_documents_semantic = results.get("related_documents", [])

        if not related_nodes_semantic and not related_documents_semantic:
            logger.warning("No related nodes or documents found from semantic search.")
            return {
                "input": query_text,
                "extracted_hierarchy": None,
                "node_information": None,
                "related_documents": [],
                "related_nodes": [],
                "relationships": [],
            }

        # Format output
        return {
            "input": query_text,
            "extracted_hierarchy": None,
            "node_information": None,
            "related_documents": [
                self.format_node(doc) for doc in related_documents_semantic
            ],
            "related_nodes": [
                self.format_node(node) for node in related_nodes_semantic
            ],
            "relationships": [],
        }

    def _collect_related_nodes(self, seed_ids: list[str]) -> list[dict[str, Any]]:
        """Gom node đích/seed + cha + con + con cháu, khử trùng theo node_id.

        Node `Document` bị loại khỏi `related_nodes` vì đã phản ánh trong `related_documents`.

        Args:
            seed_ids: Danh sách node_id gốc đã chạm được.

        Returns:
            Danh sách node theo thứ tự: seed trước, rồi cha, con, con cháu.
        """
        collected: dict[str, dict[str, Any]] = {}

        def add(node: Optional[dict[str, Any]]) -> None:
            """Thêm node vào tập kết quả nếu hợp lệ và chưa có."""
            if not node:
                return
            node_id = node.get("node_id")
            if not node_id or node_id in collected:
                return
            if node.get("label") == "Document":
                return
            collected[node_id] = node

        for seed_id in seed_ids:
            if not seed_id:
                continue
            add(self._service.get_node_by_id(seed_id))
            for ancestor in self._service.get_breadcrumbs(seed_id):
                add(ancestor)
            for child in self._service.get_children(seed_id):
                add(child)
            for descendant in self._service.get_descendants(
                seed_id, max_depth=5, limit=200
            ):
                add(descendant)

        return list(collected.values())

    def _collect_legal_relationships(
        self, seed_ids: list[str]
    ) -> list[tuple[str, dict[str, Any]]]:
        """Lấy quan hệ pháp lý của từng seed, gắn kèm node gốc để định hướng cạnh.

        Args:
            seed_ids: Danh sách node_id gốc.

        Returns:
            Danh sách cặp (node_id gốc, bản ghi quan hệ).
        """
        relationships: list[tuple[str, dict[str, Any]]] = []
        for seed_id in seed_ids:
            if not seed_id:
                continue
            for relationship in self._service.get_related_laws(seed_id, limit=50):
                relationships.append((seed_id, relationship))
        return relationships

    def _collect_related_documents(
        self,
        document_ids: list[str],
        nodes: list[dict[str, Any]],
        legal_relationships: list[tuple[str, dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """Gom provenance các văn bản liên quan (văn bản resolve + văn bản của node/quan hệ).

        Args:
            document_ids: Document_id khởi điểm (văn bản resolve được).
            nodes: Các node đã gom.
            legal_relationships: Các quan hệ pháp lý đã gom.

        Returns:
            Danh sách provenance đã chuẩn hoá, khử trùng theo document_id.
        """
        collected: dict[str, dict[str, Any]] = {}

        def add_document(document_id: Optional[str]) -> None:
            """Thêm provenance của một văn bản nếu chưa có."""
            if not document_id or document_id in collected:
                return
            provenance = self._service.get_document_provenance(document_id)
            if provenance:
                collected[document_id] = provenance

        for document_id in document_ids:
            add_document(document_id)
        for node in nodes:
            add_document(node.get("document_id"))
        for _, relationship in legal_relationships:
            for key in ("target_node", "source_node", "related_node"):
                related_node = relationship.get(key)
                if related_node:
                    add_document(related_node.get("document_id"))

        return list(collected.values())

    def _build_relationships(
        self,
        nodes: list[dict[str, Any]],
        legal_relationships: list[tuple[str, dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """Gộp quan hệ cấu trúc (CONTAINS) và quan hệ pháp lý thành mảng phẳng.

        Args:
            nodes: Các node đã gom (dùng `parent_id` để suy cạnh CONTAINS).
            legal_relationships: Các cặp (node gốc, bản ghi quan hệ pháp lý).

        Returns:
            Danh sách quan hệ {from_node_id, to_node_id, relationship_type}, khử trùng lặp.
        """
        collected: dict[tuple[str, str, str], dict[str, Any]] = {}

        def add(
            from_node_id: Optional[str],
            to_node_id: Optional[str],
            relationship_type: Optional[str],
        ) -> None:
            """Thêm một cạnh nếu đủ thông tin và chưa tồn tại."""
            if not from_node_id or not to_node_id or not relationship_type:
                return
            key = (from_node_id, relationship_type, to_node_id)
            if key in collected:
                return
            collected[key] = {
                "from_node_id": from_node_id,
                "to_node_id": to_node_id,
                "relationship_type": relationship_type,
            }

        # Cạnh cấu trúc CONTAINS suy từ parent_id của các node đã gom.
        for node in nodes:
            add(node.get("parent_id"), node.get("node_id"), "CONTAINS")

        # Cạnh quan hệ pháp lý (REFERENCES, IMPLEMENTS, INTERPRETED_BY...).
        for root_id, relationship in legal_relationships:
            relationship_type = relationship.get("relation_type")
            if relationship.get("direction") == "INCOMING":
                source = relationship.get("source_node") or {}
                add(source.get("node_id"), root_id, relationship_type)
            else:
                target = relationship.get("target_node") or {}
                add(root_id, target.get("node_id"), relationship_type)

        return list(collected.values())

    def _build_node_information(self, hierarchy: LegalHierarchy) -> dict[str, Any]:
        """Dựng `node_information` từ parse, map loại node sang label graph.

        Args:
            hierarchy: Phân cấp parse được.

        Returns:
            Dict gồm node_type, parent_node_type, citation_path, postfix_node_id.
        """
        info = hierarchy.get_all_info()
        return {
            "node_type": info.get("node_type"),
            "parent_node_type": info.get("parent_node_type"),
            "citation_path": info.get("citation_path"),
            "postfix_node_id": info.get("postfix_node_id"),
        }


# ---------------------------------------------------------------------------
# Chạy thử
# ---------------------------------------------------------------------------
QUERY_INPUTS = [
    "Nội dung Điều 1 theo Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013 là gì?",
    # "Điều 1 thuộc Chương I theo Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013 quy định gì?",
    # "Chương I của Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013 quy định về vấn đề gì?",
    "Điều 522 của Bộ luật Dân sự 2015 quy định về vấn đề gì?",
]


def main() -> None:
    """Khởi tạo kết nối và chạy pipeline V1 trên các câu hỏi mẫu."""
    neo4j_client = Neo4jClient()
    try:
        repository = LegalGraphRepository(db=neo4j_client)
        service = LegalGraphService(repository=repository)
        orchestrator = RetrievalOrchestrator(
            service=service,
            extractor=LegalQueryExtractor(),
        )

        for query_text in QUERY_INPUTS:
            print("=" * 100)
            print(f"CÂU HỎI: {query_text}")
            result = orchestrator.retrieve(query_text)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print()
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    main()
