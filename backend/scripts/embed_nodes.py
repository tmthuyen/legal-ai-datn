"""CLI embedding: chọn neo4j/chroma/dual, wiring qua container."""

import argparse

from src.common.container import build_embedding_pipeline


def main():
    """Đọc tham số và gọi pipeline embedding."""
    parser = argparse.ArgumentParser(
        description="Pipeline tạo embedding cho Article nodes trong Neo4j"
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Ưu tiên nạp vector từ file cache .npz nếu khớp model/dimension/corpus hash",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Batch size khi encode (mặc định lấy từ .env hoặc 8)",
    )
    parser.add_argument(
        "--index-only", action="store_true", help="Chỉ tạo/kiểm tra Vector Index"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Chạy bộ benchmark đánh giá định lượng Hit@K, MRR",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chạy thử nghiệm an toàn: chỉ test encode 5 mẫu, KHÔNG ghi Neo4j, KHÔNG tạo index",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Chỉ xử lý N Article đầu tiên (ghi Neo4j tập con để phát triển)",
    )
    parser.add_argument("--store", choices=("neo4j", "chroma", "dual"), default="neo4j")
    args = parser.parse_args()
    run, client, embedder, store_factory = build_embedding_pipeline(args)
    run(args, client, embedder, store_factory)


if __name__ == "__main__":
    main()
