"""
verify_kg_sync.py
CLI kiểm tra tính toàn vẹn và đồng bộ của Knowledge Graph và hệ thống Retrieval
trước và sau khi mở rộng thêm văn bản pháp luật mới.

Sử dụng:
    python scripts/verify_kg_sync.py
    python scripts/verify_kg_sync.py --strict
    python scripts/verify_kg_sync.py --validate-only
    python scripts/verify_kg_sync.py --sync-only
    python scripts/verify_kg_sync.py --candidate-docs BLDS_2005,LUAT_NHA_O_2014
"""

import argparse
import json
from pathlib import Path
import sys

# Đảm bảo UTF-8 console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Thêm đường dẫn backend vào sys.path
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.graph.sync_verifier import KnowledgeGraphSyncVerifier


def main():
    parser = argparse.ArgumentParser(
        description="Kiểm tra tính toàn vẹn và đồng bộ của Knowledge Graph và Retrieval."
    )
    parser.add_argument(
        "--nodes-file",
        type=str,
        default=None,
        help="Đường dẫn file nodes.json tùy chọn (mặc định: data/processed/nodes.json).",
    )
    parser.add_argument(
        "--relations-file",
        type=str,
        default=None,
        help="Đường dẫn file relations.json tùy chọn (mặc định: data/processed/relations.json).",
    )
    parser.add_argument(
        "--candidate-docs",
        type=str,
        default="",
        help="Danh sách document_id dự kiến mở rộng thêm (phân tách bởi dấu phẩy, ví dụ 'BLDS_2005,LUAT_NHA_O_2014').",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default="experiments/eval/kg_sync_report.md",
        help="Đường dẫn xuất file Markdown báo cáo.",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="experiments/eval/kg_sync_report.json",
        help="Đường dẫn xuất file JSON kết quả.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Chỉ kiểm tra cấu trúc đồ thị JSON (không check vector/chroma/npz).",
    )
    parser.add_argument(
        "--sync-only",
        action="store_true",
        help="Chỉ kiểm tra đồng bộ retrieval (không validate đồ thị chi tiết).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Chế độ nghiêm ngặt: coi WARN, UNKNOWN hoặc OFFLINE là lỗi FAIL và thoát với mã lỗi non-zero.",
    )
    args = parser.parse_args()

    verifier = KnowledgeGraphSyncVerifier(backend_dir=backend_dir)
    nodes_path = Path(args.nodes_file) if args.nodes_file else None
    relations_path = Path(args.relations_file) if args.relations_file else None

    candidate_docs = [d.strip() for d in args.candidate_docs.split(",") if d.strip()]

    print("=" * 80)
    print("       KIỂM ĐỊNH & ĐỐI SOÁT ĐỒNG BỘ KNOWLEDGE GRAPH (LEGAL-AI DATN)")
    print(f"       Chế độ nghiêm ngặt (--strict): {args.strict}")
    print("=" * 80)

    if args.validate_only:
        print(">> [CHẾ ĐỘ] Chỉ kiểm định tính toàn vẹn dữ liệu JSON...")
        res = verifier.validate_graph_data(nodes_path, relations_path)
        print(f">> Trạng thái: {res['status']}")
        if res["errors"]:
            print(f"❌ Có {len(res['errors'])} lỗi:")
            for err in res["errors"]:
                print(f"   - {err}")
            sys.exit(1)
        elif res["warnings"] and args.strict:
            print(f"⚠️ Có {len(res['warnings'])} cảnh báo (Strict mode coi là lỗi):")
            for w in res["warnings"]:
                print(f"   - {w}")
            sys.exit(1)
        else:
            print("✅ Dữ liệu đồ thị hợp lệ 100%!")
            sys.exit(0)

    if args.sync_only:
        print(">> [CHẾ ĐỘ] Chỉ kiểm tra đồng bộ Retrieval đa tầng...")
        res = verifier.check_retrieval_sync(nodes_path, strict=args.strict)
        print(f">> Trạng thái: {res['status']}")
        if res["errors"]:
            print(f"❌ Có {len(res['errors'])} lỗi mất đồng bộ:")
            for err in res["errors"]:
                print(f"   - {err}")
            sys.exit(1)
        elif res["warnings"] and args.strict:
            print(f"⚠️ Có {len(res['warnings'])} cảnh báo (Strict mode coi là lỗi):")
            for w in res["warnings"]:
                print(f"   - {w}")
            sys.exit(1)
        else:
            print("✅ Các kho lưu trữ retrieval hoàn toàn đồng bộ!")
            sys.exit(0)

    # Chạy kiểm tra toàn diện
    print(">> Đang thực hiện kiểm tra toàn diện 3 cấp độ:")
    print("   1. Schema, phân cấp pháp luật & quan hệ CONTAINS...")
    print("   2. Đối soát đồng bộ Article IDs & Hash giữa nodes.json, NPZ, ChromaDB, Neo4j...")
    print("   3. Phân tích liên kết chéo và dẫn chiếu chưa giải quyết...")

    report = verifier.generate_full_report(
        nodes_path=nodes_path,
        relations_path=relations_path,
        candidate_doc_ids=candidate_docs,
        strict=args.strict,
    )

    # Xuất báo cáo JSON
    json_out = backend_dir / args.output_json
    json_out.parent.mkdir(parents=True, exist_ok=True)
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Xuất báo cáo Markdown
    md_out = backend_dir / args.output_md
    verifier.export_markdown_report(report, md_out)

    print("\n" + "=" * 80)
    print(f"KẾT QUẢ KIỂM ĐỊNH TỔNG THỂ: {report['overall_status']}")
    print("=" * 80)
    print(f" - Graph Validation: {report['validation']['status']}")
    print(f" - Retrieval Sync   : {report['retrieval_synchronization']['status']}")
    print(f" - Quan hệ đủ 2 đầu kích hoạt : {len(report['unresolved_references_analysis']['resolvable_doc_relations'])}")
    print(f" - Quan hệ cần rà soát thêm   : {len(report['unresolved_references_analysis']['candidate_review_doc_relations'])}")
    print(f" - Dẫn chiếu điều đủ 2 đầu     : {len(report['unresolved_references_analysis']['resolvable_article_references'])}")
    print(f" - Dẫn chiếu chờ thêm node điều: {len(report['unresolved_references_analysis']['candidate_review_article_references'])}")

    print(f"\n>> Đã xuất báo cáo chi tiết:")
    print(f"   - Markdown: {md_out}")
    print(f"   - JSON    : {json_out}")

    if report["overall_status"] == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
