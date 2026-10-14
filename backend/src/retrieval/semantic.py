"""
semantic.py
Module tìm kiếm ngữ nghĩa độc lập (Semantic Retrieval Service) cho đồ án Pháp luật AI.

Nhiệm vụ:
- Tiếp nhận câu truy vấn pháp lý (question_text hoặc query thô từ người dùng).
- Chuyển đổi query thành dense vector 1024-d bằng NodeEmbedder (mặc định darklethelong/vnlegal-lal).
- Truy vấn trực tiếp chỉ mục vector (db.index.vector.queryNodes) trên Neo4j.
- Trả về danh sách ứng viên Article nodes được chuẩn hóa theo Unified Data Contract
  cho Hybrid Retrieval và Graph Traversal:
    - rank, node_id, type, score, document_id, title, full_text, parent_id
    - retrieval_source: "vector" (chứng thực nguồn gốc)
    - hop: 0 (seed node mầm, chưa traverse graph)
"""

import sys
import time
import logging
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
                        "rank": int,
                        "node_id": str,
                        "type": str,
                        "score": float,
                        "document_id": str,
                        "title": str,
                        "full_text": str,
                        "parent_id": str,
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
                   node.type AS type,
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
                results.append(
                    {
                        "rank": rank,
                        "node_id": r.get("node_id"),
                        "type": r.get("type") or "Article",
                        "score": round(float(r.get("score", 0.0)), 4),
                        "document_id": r.get("document_id"),
                        "title": r.get("title"),
                        "full_text": r.get("full_text"),
                        "parent_id": r.get("parent_id"),
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
