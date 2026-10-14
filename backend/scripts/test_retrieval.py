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
import os
import sys
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

from src.common.schemas import LegalHierarchy
from src.graph.embedder import NodeEmbedder
from src.graph.graph_repository import LegalGraphRepository
from src.graph.graph_service import LegalGraphService
from src.graph.neo4j_client import Neo4jClient
from src.retrieval.legal_query_extractor import LegalQueryExtractor
from src.retrieval.retrieval_service import RetrievalService
from src.retrieval.semantic import SemanticSearcher
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


# ---------------------------------------------------------------------------
# Chạy thử
# ---------------------------------------------------------------------------
QUERY_INPUTS = [
    "Nội dung Điều 1 theo Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013 là gì?",
    "Điều 1 thuộc Chương I theo Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013 quy định gì?",
    # "Chương I của Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013 quy định về vấn đề gì?",
    "Điều 522 của Bộ luật Dân sự 2015 quy định về vấn đề gì?",
]


def main() -> None:
    """Khởi tạo kết nối và chạy pipeline V1 trên các câu hỏi mẫu."""
    neo4j_client = Neo4jClient()
    try:
        repository = LegalGraphRepository(db=neo4j_client)
        service = LegalGraphService(repository=repository)

        model_name = os.getenv("EMBEDDING_MODEL_NAME")
        batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", 4))
        device = os.getenv("EMBEDDING_DEVICE", "cpu")

        # Embedding service
        embedder = NodeEmbedder(
            model_name=model_name,
            batch_size=batch_size,
            device=device,
            max_seq_length=2048,
        )

        # Semantic search service
        semantic_service = SemanticSearcher(
            neo4j_client=neo4j_client, embedder=embedder
        )

        # Retrieval service
        retrieval_service = RetrievalService(
            legal_graph_service=service,
            legal_query_extractor=LegalQueryExtractor(),
            semantic_service=semantic_service,
        )

        for query_text in QUERY_INPUTS:
            print("=" * 100)
            print(f"CÂU HỎI: {query_text}")
            result = retrieval_service.retrieve(query_text)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print()
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    main()
