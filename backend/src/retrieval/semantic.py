"""
semantic.py
Module tìm kiếm ngữ nghĩa độc lập (Semantic Retrieval Service) cho đồ án Pháp luật AI.

Nhiệm vụ:
- Tiếp nhận câu truy vấn pháp lý (question_text hoặc query thô từ người dùng).
- Chuyển đổi query thành dense vector 1024-d bằng NodeEmbedder (mặc định darklethelong/vnlegal-lal).
- Truy vấn trực tiếp chỉ mục vector (db.index.vector.queryNodes) trên Neo4j.
- Trả về danh sách ứng viên Article nodes được chuẩn hóa theo Unified Data Contract
  cho Hybrid Retrieval và Graph Traversal:
    - node_id, label, number, title, full_text, document_id, parent_id
    - rank, score, retrieval_source: "vector", hop: 0
"""

import sys
import time
import logging
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

try:
    from src.graph.embedder import NodeEmbedder
    from src.graph.neo4j_client import Neo4jClient
except (ImportError, ModuleNotFoundError):
    from graph.embedder import NodeEmbedder  # type: ignore
    from graph.neo4j_client import Neo4jClient  # type: ignore

logger = logging.getLogger(__name__)

CANONICAL_LABELS: Dict[str, str] = {
    "document": "Document",
    "part": "Part",
    "chapter": "Chapter",
    "section": "Section",
    "subsection": "SubSection",
    "article": "Article",
    "clause": "Clause",
    "point": "Point",
}


class SemanticSearcher:
    """
    Truy vấn trực tiếp chỉ mục Vector trên Neo4j.
    """

    def __init__(
        self,
        embedder: Optional[NodeEmbedder] = None,
        neo4j_client: Optional[Neo4jClient] = None,
        index_name: str = "article_embeddings_idx",
    ):
        self.embedder = embedder or NodeEmbedder()
        self.client = neo4j_client or Neo4jClient()
        self.index_name = index_name

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Tìm kiếm các điều luật liên quan nhất theo ngữ nghĩa trên Neo4j Vector Index.

        Args:
            query: Nội dung câu hỏi truy vấn của người dùng.
            top_k: Số lượng kết quả hàng đầu cần trả về.
            document_filter: Tuỳ chọn lọc theo văn bản cụ thể (ví dụ: 'BLDS_2015').

        Returns:
            Dict chuẩn hóa theo Unified Contract:
            {
                "query": str,
                "total_found": int,
                "search_time_ms": float,
                "encode_time_ms": float,
                "model_name": str,
                "results": [
                    {
                        "node_id": str,
                        "label": str,
                        "number": Any,
                        "title": str,
                        "full_text": str,
                        "document_id": str,
                        "parent_id": str,
                        "rank": int,
                        "score": float,
                        "retrieval_source": "vector",
                        "hop": 0
                    },
                    ...
                ]
            }
        """
        if not query or not query.strip():
            return {
                "query": query,
                "total_found": 0,
                "search_time_ms": 0.0,
                "encode_time_ms": 0.0,
                "model_name": self.embedder.model_name,
                "results": [],
            }

        t_start = time.time()

        # 1. Mã hóa câu hỏi thành dense vector
        t_enc = time.time()
        query_vector = self.embedder.encode_query(query)
        encode_time_ms = (time.time() - t_enc) * 1000

        results: List[Dict[str, Any]] = []

        # 2. Truy vấn qua Neo4j Vector Index
        try:
            where_filter = ""
            candidate_k = top_k
            if document_filter:
                where_filter = "WHERE node.document_id = $document_filter"
                # Mở rộng candidate pool gấp 10 lần để tránh hiện tượng filter sau khi cắt top_k làm cạn kiệt kết quả
                candidate_k = max(top_k * 10, 50)

            cypher_params: Dict[str, Any] = {
                "candidate_k": candidate_k,
                "top_k": top_k,
                "query_vector": query_vector,
            }
            if document_filter:
                cypher_params["document_filter"] = document_filter

            search_cypher = f"""
            CALL db.index.vector.queryNodes('{self.index_name}', $candidate_k, $query_vector)
            YIELD node, score
            {where_filter}
            RETURN node.node_id AS node_id,
                   coalesce(node.label, head([lbl IN labels(node) WHERE lbl <> 'LegalNode']), 'Article') AS label,
                   node.number AS number,
                   node.title AS title,
                   node.full_text AS full_text,
                   node.document_id AS document_id,
                   node.parent_id AS parent_id,
                   score
            ORDER BY score DESC
            LIMIT $top_k
            """
            rows = self.client.execute_read(
                search_cypher,
                cypher_params,
            )
            for rank, r in enumerate(rows, 1):
                lbl = r.get("label") or "Article"
                results.append(
                    {
                        "node_id": r.get("node_id"),
                        "label": lbl,
                        "number": r.get("number"),
                        "title": r.get("title"),
                        "full_text": r.get("full_text"),
                        "document_id": r.get("document_id"),
                        "parent_id": r.get("parent_id"),
                        "rank": rank,
                        "score": round(float(r.get("score", 0.0)), 4),
                        "retrieval_source": "vector",
                        "hop": 0,
                    }
                )
        except Exception as e:
            logger.error("Lỗi khi truy vấn Neo4j Vector Index '%s': %s", self.index_name, e)

        total_time_ms = (time.time() - t_start) * 1000

        return {
            "query": query,
            "total_found": len(results),
            "search_time_ms": round(total_time_ms, 2),
            "encode_time_ms": round(encode_time_ms, 2),
            "model_name": self.embedder.model_name,
            "results": results,
        }

    def search_node_ids(self, query: str, top_k: int = 5) -> List[str]:
        """
        Hàm tiện ích chỉ trả về danh sách ID của các node liên quan nhất
        (phục vụ Graph Traverse và Reranker trong hybrid search).
        """
        res = self.search(query=query, top_k=top_k)
        return [item["node_id"] for item in res.get("results", [])]

    def semantic_search_by_text_and_label(
        self,
        text: str,
        label: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm node theo nội dung text và loại node (label).
        Mục đích: Tìm node động (ví dụ: 'Bộ luật dân sự', 'Document') để lấy document_id
        hoặc node_id tương ứng mà không cần hard-code (như 'BLDS_2015').

        Args:
            text: Chuỗi văn bản cần tìm kiếm (ví dụ: 'Bộ luật dân sự', 'Hiến pháp').
            label: Loại node / nhãn cấp bậc (ví dụ: 'Document', 'Chapter', 'Article', 'Part').
            top_k: Số lượng node phù hợp nhất cần trả về.

        Returns:
            Danh sách node khớp nhất, chuẩn hóa theo Unified Contract:
            [
                {
                    "node_id": str,
                    "label": str,
                    "number": Any,
                    "title": str,
                    "full_text": str,
                    "document_id": str,
                    "parent_id": str,
                    "rank": int,
                    "score": float,
                    "retrieval_source": str,  # "vector" khi label="Article", "text_label" khi là các label khác
                    "hop": 0
                },
                ...
            ]
        """
        if not text or not text.strip() or not label or not label.strip():
            return []

        # 1. Chuẩn hóa và validate canonical label (ví dụ: 'document' -> 'Document', 'ARTICLE' -> 'Article')
        raw_label = label.strip().lower()
        target_label = CANONICAL_LABELS.get(raw_label)
        if not target_label:
            logger.warning("Nhãn '%s' không hợp lệ hoặc không được hỗ trợ trong Knowledge Graph.", label)
            return []

        clean_text = text.strip()

        # 2. Nếu label là 'Article' và đã có vector index trong Neo4j, tái sử dụng search() (retrieval_source="vector")
        if target_label == "Article":
            search_res = self.search(query=clean_text, top_k=top_k)
            return search_res.get("results", [])

        # 3. Truy vấn danh sách node thuộc canonical label từ Neo4j
        cypher = """
        MATCH (n:LegalNode)
        WHERE $label IN labels(n) OR n.label = $label
        RETURN n.node_id AS node_id,
               coalesce(n.label, head([lbl IN labels(n) WHERE lbl <> 'LegalNode']), $label) AS label,
               n.number AS number,
               n.title AS title,
               coalesce(n.full_text, n.text, '') AS full_text,
               n.document_id AS document_id,
               n.parent_id AS parent_id
        """
        try:
            rows = self.client.execute_read(cypher, {"label": target_label})
        except Exception as e:
            logger.error("Lỗi khi truy vấn node theo nhãn '%s': %s", target_label, e)
            rows = []

        if not rows:
            return []

        # 4. Tính điểm lexical matching + fuzzy matching nhẹ (không encode neural embedding)
        candidates_scored = []
        q_lower = clean_text.lower()

        for r in rows:
            node_title = (r.get("title") or "").strip()
            node_full_text = (r.get("full_text") or "").strip()
            t_lower = node_title.lower()

            # Ưu tiên so khớp trên title
            score = 0.0
            if q_lower and t_lower:
                if q_lower == t_lower:
                    score = 1.0
                elif q_lower in t_lower:
                    score = 0.75 + 0.25 * (len(q_lower) / len(t_lower))
                elif t_lower in q_lower:
                    score = 0.70 + 0.25 * (len(t_lower) / len(q_lower))
                else:
                    score = SequenceMatcher(None, q_lower, t_lower).ratio()

            # Fallback so khớp trên full_text / text nếu title không khớp hoặc rỗng
            if score < 0.5 and node_full_text:
                ft_lower = node_full_text[:300].lower()
                if q_lower in ft_lower:
                    score = max(score, 0.60)
                else:
                    ft_ratio = SequenceMatcher(None, q_lower, ft_lower[:len(q_lower) * 2]).ratio()
                    score = max(score, ft_ratio * 0.5)

            if score > 0.0:
                candidates_scored.append((score, r))

        # Sắp xếp theo điểm giảm dần
        candidates_scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for rank, (score, r) in enumerate(candidates_scored[:top_k], 1):
            lbl = r.get("label") or target_label
            results.append(
                {
                    "node_id": r.get("node_id"),
                    "label": lbl,
                    "number": r.get("number"),
                    "title": r.get("title"),
                    "full_text": r.get("full_text"),
                    "document_id": r.get("document_id"),
                    "parent_id": r.get("parent_id"),
                    "rank": rank,
                    "score": round(float(score), 4),
                    "retrieval_source": "text_label",
                    "hop": 0,
                }
            )
        return results
