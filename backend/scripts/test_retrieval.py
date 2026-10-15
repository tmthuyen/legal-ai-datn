"""
test_retrieval.py
Script chạy thủ công pipeline Retrieval V1: Parse -> Validate -> Resolve -> Graph Retrieval.

Script chỉ là client mỏng: logic nghiệp vụ và wiring service nằm trong `src/`
(`src/common/container.py` + `src/retrieval/retrieval_service.py`).

Chạy (từ thư mục `backend/`):
    python scripts/test_retrieval.py
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.common.container import build_services

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

QUERY_INPUTS = [
    "Nội dung Điều 1 theo Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013 là gì?",
    "Điều 1 thuộc Chương I theo Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013 quy định gì?",
    # "Chương I của Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013 quy định về vấn đề gì?",
    "Điều 522 của Bộ luật Dân sự 2015 quy định về vấn đề gì?",
]


def main() -> None:
    """Khởi tạo service dùng chung và chạy pipeline V1 trên các câu hỏi mẫu."""
    import psutil

    services = build_services()
    process = psutil.Process(os.getpid())
    try:
        print(f"RAM process: {process.memory_info().rss / 1024**3:.2f} GB")

        for query_text in QUERY_INPUTS:
            print("=" * 100)
            print(f"CÂU HỎI: {query_text}")
            result = services.retrieval_service.retrieve(query_text)
            print(json.dumps(result, ensure_ascii=False, indent=2))

            print(f"RAM process: {process.memory_info().rss / 1024**3:.2f} GB")
            print()
    finally:
        services.close()


if __name__ == "__main__":
    main()
