"""
runner_eval.py
Runner thực thi đánh giá so sánh đối đầu (Ablation Study) giữa ba phương pháp truy xuất:
1. Lexical Retrieval (BM25)
2. Dense Semantic Retrieval (Embedding darklethelong/vnlegal-lal)
3. Hybrid Retrieval (BM25 + Semantic kết hợp qua Reciprocal Rank Fusion - RRF)

Nhiệm vụ:
- Đảm bảo tính công bằng: chạy trên cùng tập dữ liệu, cùng top_k.
- Đánh giá trước Graph Traversal (không gọi LLM, không duyệt sâu).
- Phân biệt lỗi kết nối/hệ thống (ERROR) với trường hợp tìm kiếm không ra kết quả (NO_RESULTS).
- Xuất báo cáo chi tiết CSV, JSON tổng hợp và bảng so sánh Markdown.
"""

import argparse
import csv
import datetime
import json
import statistics
import logging
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

# Thiết lập encoding UTF-8 cho Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.eval.dataset_eval import EvalQuery, EvaluationDatasetLoader
from src.eval.metrics_eval import compute_evaluation_report, evaluate_single_query
from src.graph.embedder import NodeEmbedder
from src.graph.neo4j_client import Neo4jClient
from src.retrieval.hybrid import BM25Searcher, HybridSearcher
from src.retrieval.semantic import SemanticSearcher
from src.utils.logger import setup_logger
from src.vector.chroma_store import ChromaVectorStore

logger = setup_logger("eval_runner", "eval_runner.log")


class StandaloneGraphHydrator:
    """Client dự phòng đọc từ nodes.json khi Neo4j server offline."""

    def __init__(self, node_map: Dict[str, Dict[str, Any]]):
        self.node_map = node_map

    def execute_read(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self.execute_query(query, params)

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not params or "hits" not in params:
            return []
        hits = params["hits"]
        doc_filter = params.get("document_filter")
        rows = []
        for h in hits:
            nid = h.get("node_id")
            n = self.node_map.get(nid, {})
            if doc_filter and n.get("document_id") != doc_filter:
                continue
            rows.append({
                "node_id": nid,
                "label": n.get("label") or n.get("type") or "Article",
                "number": n.get("number"),
                "title": n.get("title") or "",
                "full_text": n.get("full_text") or n.get("text") or "",
                "document_id": n.get("document_id"),
                "parent_id": n.get("parent_id"),
                "score": h.get("score", 0.0),
                "doc_node_id": n.get("document_id"),
                "doc_label": "Document",
                "doc_title": "",
                "doc_full_text": "",
                "doc_document_id": n.get("document_id"),
                "doc_parent_id": None,
            })
        return rows


class NpzVectorStore:
    """Vector store dự phòng chạy trực tiếp trên ma trận vector nén .npz."""

    def __init__(self, npz_path: Path, node_map: Dict[str, Dict[str, Any]]):
        with np.load(npz_path, allow_pickle=True) as data:
            self.node_ids = [str(x) for x in data["node_ids"]]
            self.vectors = np.array(data["vectors"], dtype=np.float32)
        if len(self.node_ids) != len(self.vectors) or self.vectors.ndim != 2:
            raise ValueError("NPZ sai cấu trúc: node_ids và vectors không khớp")
        self.node_map = node_map
        # Chuẩn hóa L2 norm
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.vectors = self.vectors / norms

    def query(self, vector: List[float], top_k: int = 5, document_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        q_vec = np.array(vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm
        if self.vectors.shape[1] != q_vec.shape[0]:
            raise ValueError("Embedding dimension không trùng với NPZ")
        sims = np.dot(self.vectors, q_vec)
        if document_filter:
            mask = np.array([self.node_map.get(nid, {}).get("document_id") == document_filter for nid in self.node_ids])
            sims[~mask] = -1e9
        valid_indices = np.where(sims > -1e8)[0]
        top_indices = valid_indices[np.argsort(sims[valid_indices])[::-1][:top_k]]
        hits = []
        for idx in top_indices:
            nid = self.node_ids[idx]
            sim = float(sims[idx])
            score = max(0.0, min(1.0, (1.0 + sim) / 2.0))
            hits.append({"node_id": nid, "score": score, "metadata": self.node_map.get(nid, {})})
        return hits


class RetrievalEvaluator:
    """Điều phối và thực thi đánh giá Retrieval độc lập cho 3 phương pháp."""

    def __init__(
        self,
        backend_dir: Optional[Path] = None,
        chroma_path: Optional[Path] = None,
        embedding_model: str = "darklethelong/vnlegal-lal",
        rrf_k: int = 60,
    ):
        if backend_dir is None:
            backend_dir = Path(__file__).resolve().parents[2]
        self.backend_dir = Path(backend_dir)
        self.chroma_path = Path(chroma_path or (self.backend_dir / "data" / "chroma"))
        self.npz_path = (
            self.backend_dir
            / "data"
            / "embeddings"
            / "article_embeddings_darklethelong_vnlegal-lal_enriched.npz"
        )
        self.embedding_model = embedding_model
        self.rrf_k = rrf_k
        self.backend_info = {}

        # Nạp node_map từ file dự phòng nodes.json
        self.nodes_file = self.backend_dir / "data" / "processed" / "nodes.json"
        self.node_map = {}
        if self.nodes_file.exists():
            with open(self.nodes_file, "r", encoding="utf-8") as f:
                nodes_list = json.load(f)
            self.node_map = {n["node_id"]: n for n in nodes_list}

        # Khởi tạo các searchers
        self.neo4j_client = self._init_neo4j_client()
        self.embedder = self._init_embedder()
        self.vector_store = self._init_vector_store()

        self.bm25_searcher = self._init_bm25()
        self.semantic_searcher = self._init_semantic()
        self.hybrid_searcher = self._init_hybrid()

    def _init_neo4j_client(self) -> Any:
        try:
            client = Neo4jClient()
            # Constructor có thể không kiểm tra kết nối ngay, cần chạy query thực sự.
            client.execute_read("RETURN 1 AS ok")
            self.backend_info["graph"] = "neo4j"
            logger.info("Đã kết nối Neo4j thành công cho Evaluation.")
            return client
        except Exception as e:
            logger.warning(
                "Không thể kết nối Neo4j: %s. Chuyển sang chế độ Standalone (đọc dữ liệu từ nodes.json).",
                e,
            )
            self.backend_info["graph"] = "nodes_json_fallback"
            return StandaloneGraphHydrator(self.node_map)

    def _init_embedder(self) -> NodeEmbedder:
        logger.info("Nạp NodeEmbedder: %s", self.embedding_model)
        embedder = NodeEmbedder(model_name=self.embedding_model)
        embedder.load_model()
        return embedder

    def _init_vector_store(self) -> Any:
        # Thử mở ChromaVectorStore
        if self.chroma_path.exists():
            try:
                store = ChromaVectorStore(
                    path=self.chroma_path,
                    collection_name="legal_articles",
                    model_name=self.embedding_model,
                    dimension=1024,
                    create=False,
                )
                if store.count() <= 0:
                    raise ValueError("Chroma collection rỗng")
                self.backend_info["vector"] = "chroma"
                logger.info("Đã mở ChromaVectorStore: %d Article vectors.", store.count())
                return store
            except Exception as e:
                logger.warning("Không thể mở ChromaVectorStore (%s). Thử nạp từ NPZ cache...", e)

        # Fallback nạp ma trận vector .npz
        if self.npz_path.exists():
            try:
                npz_store = NpzVectorStore(self.npz_path, self.node_map)
                self.backend_info["vector"] = "npz_fallback"
                logger.info("Đã nạp NpzVectorStore: %d Article vectors.", len(npz_store.node_ids))
                return npz_store
            except Exception as e:
                logger.error("Lỗi khi nạp NPZ vector cache: %s", e)

        self.backend_info["vector"] = "none"
        logger.error("Không tìm thấy cả Chroma lẫn NPZ vector store!")
        return None

    def _init_bm25(self) -> BM25Searcher:
        logger.info("Khởi tạo BM25Searcher...")
        client = self.neo4j_client if isinstance(self.neo4j_client, Neo4jClient) else None
        searcher = BM25Searcher(neo4j_client=client, corpus_path=self.nodes_file)
        self.backend_info["bm25_corpus_size"] = len(searcher.articles)
        self.backend_info["bm25_corpus_ids"] = [str(a.get("node_id")) for a in searcher.articles if a.get("node_id")]
        return searcher

    def _init_semantic(self) -> SemanticSearcher:
        logger.info("Khởi tạo SemanticSearcher...")
        return SemanticSearcher(
            embedder=self.embedder,
            neo4j_client=self.neo4j_client,
            vector_store=self.vector_store,
        )

    def _init_hybrid(self) -> HybridSearcher:
        logger.info("Khởi tạo HybridSearcher (RRF k=%d)...", self.rrf_k)
        return HybridSearcher(
            semantic_searcher=self.semantic_searcher,
            bm25_searcher=self.bm25_searcher,
            default_rrf_k=self.rrf_k,
        )

    def evaluate_query(
        self,
        searcher_instance: Any,
        query: EvalQuery,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """Thực thi một câu hỏi trên một retriever và ghi nhận metrics."""
        t_start = time.perf_counter()
        status = "SUCCESS"
        error_msg = None
        retrieved_ids: List[str] = []
        scores: List[float] = []

        try:
            res = searcher_instance.search(query=query.question, top_k=top_k)
            if not isinstance(res, dict):
                raise TypeError("Searcher trả về kết quả không phải dict")
            nodes = res.get("related_nodes", [])
            if not nodes:
                status = "NO_RESULTS"
            else:
                for n in nodes:
                    nid = n.get("node_id")
                    if nid:
                        retrieved_ids.append(nid)
                        scores.append(n.get("score", 0.0))
        except Exception as e:
            status = "ERROR"
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error("Lỗi khi tìm kiếm query %s: %s", query.query_id, error_msg)

        latency_ms = (time.perf_counter() - t_start) * 1000

        record = evaluate_single_query(
            query_id=query.query_id,
            question=query.question,
            hop_type=query.hop_type,
            retrieved_ids=retrieved_ids,
            ground_truth_ids=query.ground_truth_node_ids,
            latency_ms=latency_ms,
            status=status,
            error_message=error_msg,
            scores=scores,
        )
        return record

    def run_benchmark(
        self,
        queries: List[EvalQuery],
        methods: Optional[List[str]] = None,
        top_k: int = 10,
    ) -> Dict[str, Dict[str, Any]]:
        """Chạy kiểm thử toàn bộ dataset trên các phương pháp được chỉ định."""
        results: Dict[str, Dict[str, Any]] = {}
        methods = methods or ["bm25", "semantic", "hybrid"]

        searcher_map = {
            "bm25": ("BM25 (Lexical)", self.bm25_searcher),
            "semantic": ("Semantic (Dense Vector)", self.semantic_searcher),
            "hybrid": ("Hybrid (BM25 + Semantic RRF)", self.hybrid_searcher),
        }

        for method_key in methods:
            if method_key not in searcher_map:
                logger.warning("Bỏ qua phương pháp không hỗ trợ: %s", method_key)
                continue

            display_name, searcher = searcher_map[method_key]
            print(f"\n{'='*75}")
            print(f">> Đang chạy đánh giá: {display_name} (Top-K = {top_k})...")
            print(f"{'='*75}")

            query_records = []
            for i, q in enumerate(queries, start=1):
                rec = self.evaluate_query(searcher, q, top_k=top_k)
                rec["method"] = method_key
                query_records.append(rec)
                if i % 10 == 0 or i == len(queries):
                    print(f"   Đã xử lý {i}/{len(queries)} câu...")

            report = compute_evaluation_report(query_records)
            results[method_key] = report

        return results


def export_evaluation_results(
    results: Dict[str, Dict[str, Any]],
    validation_report: Dict[str, Any],
    output_dir: Path,
    top_k: int = 10,
) -> Tuple[Path, Path, Path]:
    """Xuất kết quả ra CSV chi tiết, JSON tổng hợp và file Markdown báo cáo."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Xuất file CSV chi tiết
    csv_path = output_dir / f"retrieval_evaluation_detailed_{timestamp_str}.csv"
    fieldnames = [
        "method",
        "query_id",
        "hop_type",
        "status",
        "first_hit_rank",
        "hit@1",
        "hit@5",
        "hit@10",
        "recall@1",
        "recall@5",
        "recall@10",
        "mrr@10",
        "ndcg@10",
        "latency_ms",
        "ground_truth_ids",
        "predicted_ids",
        "question",
        "error_message",
    ]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for method, report in results.items():
            for q in report.get("queries", []):
                row = {
                    "method": method,
                    "query_id": q["query_id"],
                    "hop_type": q["hop_type"],
                    "status": q["status"],
                    "first_hit_rank": q["first_hit_rank"] or "",
                    "hit@1": q["hit@1"],
                    "hit@5": q["hit@5"],
                    "hit@10": q["hit@10"],
                    "recall@1": q["recall@1"],
                    "recall@5": q["recall@5"],
                    "recall@10": q["recall@10"],
                    "mrr@10": q["mrr@10"],
                    "ndcg@10": q["ndcg@10"],
                    "latency_ms": q["latency_ms"],
                    "ground_truth_ids": ";".join(q["ground_truth_ids"]),
                    "predicted_ids": ";".join(q["predicted_ids"]),
                    "question": q["question"],
                    "error_message": q["error_message"],
                }
                writer.writerow(row)

    # 2. Xuất file JSON tổng hợp
    json_path = output_dir / f"retrieval_evaluation_summary_{timestamp_str}.json"
    summary_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "top_k": top_k,
        "validation_report": validation_report,
        "overall_summary": {
            method: rep["overall"] for method, rep in results.items()
        },
        "by_hop_type_summary": {
            method: rep["by_hop_type"] for method, rep in results.items()
        },
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)

    # 3. Xuất file Markdown báo cáo
    md_path = output_dir / f"retrieval_evaluation_report_{timestamp_str}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Báo Cáo Thực Nghiệm Đánh Giá Retrieval (Ablation Study)\n\n")
        f.write(f"- **Thời gian thực nghiệm:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **Tập dữ liệu:** `{validation_report.get('dataset_file')}` ({validation_report.get('total_queries')} câu hỏi)\n")
        f.write(f"- **Phân bố độ phức tạp:** `{validation_report.get('hop_type_distribution')}`\n")
        f.write(f"- **Ngưỡng cắt Top-K:** {top_k}\n\n")

        f.write("## 1. Bảng So Sánh Hiệu Năng Tổng Thể (Overall Performance)\n\n")
        f.write("| Phương pháp | Hit@1 (%) | Hit@5 (%) | Hit@10 (%) | Recall@1 (%) | Recall@5 (%) | Recall@10 (%) | MRR@10 | NDCG@10 | Latency TB (ms) |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")

        for m_key, m_name in [
            ("bm25", "BM25 (Lexical)"),
            ("semantic", "Dense Semantic (vnlegal-lal)"),
            ("hybrid", "**Hybrid (BM25 + Semantic RRF)**"),
        ]:
            if m_key in results:
                ov = results[m_key]["overall"]
                f.write(
                    f"| {m_name} | {ov['hit@1']}% | {ov['hit@5']}% | {ov['hit@10']}% | "
                    f"{ov['recall@1']}% | {ov['recall@5']}% | {ov['recall@10']}% | "
                    f"{ov['mrr@10']:.4f} | {ov['ndcg@10']:.4f} | {ov['avg_latency_ms']} ms |\n"
                )

        f.write("\n## 2. Phân Tích Chi Tiết Theo Hop Type (Độ phức tạp truy xuất)\n\n")
        all_hops = sorted(validation_report.get("hop_type_distribution", {}).keys())
        for ht in all_hops:
            f.write(f"### Nhóm: `{ht}`\n\n")
            f.write("| Phương pháp | Hit@1 (%) | Hit@5 (%) | Hit@10 (%) | Recall@5 (%) | Recall@10 (%) | MRR@10 |\n")
            f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
            for m_key, m_name in [
                ("bm25", "BM25"),
                ("semantic", "Semantic"),
                ("hybrid", "**Hybrid RRF**"),
            ]:
                if m_key in results and ht in results[m_key]["by_hop_type"]:
                    sub = results[m_key]["by_hop_type"][ht]
                    f.write(
                        f"| {m_name} | {sub['hit@1']}% | {sub['hit@5']}% | {sub['hit@10']}% | "
                        f"{sub['recall@5']}% | {sub['recall@10']}% | {sub['mrr@10']:.4f} |\n"
                    )
            f.write("\n")

        f.write("## 3. Nhận Xét & Kết Luận Khoa Học\n\n")
        f.write("- **BM25:** Kết quả và độ trễ được đo trên tập câu hỏi này; không suy rộng sang mọi truy vấn.\n")
        f.write("- **Dense Semantic:** So sánh các metric trong bảng; cần kiểm thử thêm để kết luận khả năng xử lý diễn đạt khác từ khóa.\n")
        if "semantic" in results and "hybrid" in results:
            sem = results["semantic"]["overall"]
            hyb = results["hybrid"]["overall"]
            for metric in ("hit@1", "hit@5", "recall@5", "recall@10", "mrr@10"):
                diff = hyb[metric] - sem[metric]
                relation = "cao hơn" if diff > 0 else ("thấp hơn" if diff < 0 else "bằng")
                f.write(f"- **Hybrid so với Semantic – {metric}:** {relation} ({hyb[metric]} so với {sem[metric]}).\n")
            f.write("- **Lưu ý:** Đây là kết quả retrieval trước graph traversal. Không thể suy ra Hybrid vượt trội trên mọi tình huống chỉ từ benchmark này.\n")

    return csv_path, json_path, md_path


def print_comparison_table(results: Dict[str, Dict[str, Any]]) -> None:
    """In bảng so sánh Markdown ra terminal."""
    print("\n" + "=" * 90)
    print("                      BẢNG TỔNG HỢP SO SÁNH HIỆU NĂNG RETRIEVAL")
    print("=" * 90)
    header = (
        f"{'Phương pháp':<28} | {'Hit@1':<7} | {'Hit@5':<7} | {'Hit@10':<7} | "
        f"{'Rec@5':<7} | {'Rec@10':<7} | {'MRR@10':<7} | {'Latency':<10}"
    )
    print(header)
    print("-" * 90)

    for m_key, m_name in [
        ("bm25", "BM25 (Lexical)"),
        ("semantic", "Semantic (vnlegal-lal)"),
        ("hybrid", "Hybrid (BM25+Sem RRF)"),
    ]:
        if m_key in results:
            ov = results[m_key]["overall"]
            row = (
                f"{m_name:<28} | {ov['hit@1']:>5.1f}% | {ov['hit@5']:>5.1f}% | {ov['hit@10']:>5.1f}% | "
                f"{ov['recall@5']:>5.1f}% | {ov['recall@10']:>5.1f}% | {ov['mrr@10']:>7.4f} | {ov['avg_latency_ms']:>6.1f} ms"
            )
            print(row)
    print("=" * 90 + "\n")


def resolve_path(path_str: str, base_dir: Path) -> Path:
    """Chuẩn hóa đường dẫn tương đối, tránh lỗi lặp backend/backend."""
    p = Path(path_str)
    if p.is_absolute():
        return p
    # Thử ghép trực tiếp
    cand1 = base_dir / p
    if cand1.exists() or cand1.parent.exists():
        return cand1
    # Nếu path_str bắt đầu bằng backend/ và base_dir kết thúc bằng backend
    if path_str.startswith("backend/") or path_str.startswith("backend\\"):
        sub = path_str[8:]
        cand2 = base_dir / sub
        if cand2.exists() or cand2.parent.exists():
            return cand2
    return cand1


def main():
    parser = argparse.ArgumentParser(description="Chạy Retrieval Evaluation độc lập (BM25 vs Semantic vs Hybrid).")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/eval/zalo_blds_scope.json",
        help="Đường dẫn file dataset JSON.",
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=10,
        help="Số lượng kết quả top-k cần lấy (mặc định: 10).",
    )
    parser.add_argument(
        "--methods",
        type=str,
        default="bm25,semantic,hybrid",
        help="Danh sách các phương pháp cần chạy (phân tách bởi dấu phẩy, ví dụ: 'bm25,semantic,hybrid').",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="experiments/eval",
        help="Thư mục xuất báo cáo CSV, JSON và Markdown.",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Yêu cầu Neo4j và Chroma, không cho phép fallback"
    )
    parser.add_argument(
        "--rrf_k",
        type=int,
        default=60,
        help="Hằng số làm mịn RRF cho Hybrid Search (mặc định: 60).",
    )
    args = parser.parse_args()

    backend_dir = Path(__file__).resolve().parents[2]
    dataset_path = resolve_path(args.dataset, backend_dir)
    output_dir = resolve_path(args.output_dir, backend_dir)

    methods = [m.strip().lower() for m in args.methods.split(",") if m.strip()]

    print(f">> Nạp dataset: {dataset_path}")
    loader = EvaluationDatasetLoader(kg_nodes_path=backend_dir / "data" / "processed" / "nodes.json")
    queries, val_report = loader.load_dataset(dataset_path)

    print(f">> Đã nạp {len(queries)} queries.")
    print(f"   Phân bố hop_type: {val_report.get('hop_type_distribution')}")
    if not val_report.get("is_valid"):
        raise ValueError(f"Dataset không hợp lệ: {val_report}")
    if val_report.get("unmatched_kg_nodes"):
        print(f"   CẢNH BÁO node không có trong KG: {val_report.get('unmatched_kg_nodes')}")

    evaluator = RetrievalEvaluator(backend_dir=backend_dir, rrf_k=args.rrf_k)
    if args.strict and (evaluator.backend_info.get("graph") != "neo4j" or evaluator.backend_info.get("vector") != "chroma"):
        raise RuntimeError(f"Strict mode yêu cầu Neo4j và Chroma thực: {evaluator.backend_info}")
    if args.top_k < 10:
        raise ValueError("Cần --top_k >= 10 vì báo cáo có Hit@10/Recall@10")
    if not evaluator.bm25_searcher.articles or evaluator.vector_store is None:
        raise RuntimeError("Không có corpus BM25 hoặc Vector Store để benchmark công bằng")
    bm_ids = set(evaluator.backend_info["bm25_corpus_ids"])
    if isinstance(evaluator.vector_store, NpzVectorStore):
        vec_ids = set(evaluator.vector_store.node_ids)
        missing = bm_ids - vec_ids
        extra = vec_ids - bm_ids
        if missing or extra:
            raise RuntimeError(f"BM25/NPZ không cùng Article corpus: BM25-only={len(missing)} Vector-only={len(extra)}; ví dụ={list(sorted(missing))[:5]}")
    else:
        collection = evaluator.vector_store.collection
        vec_ids = set()
        total = collection.count()
        for offset in range(0, total, 1000):
            page = collection.get(limit=min(1000, total - offset), offset=offset, include=[])
            vec_ids.update(page["ids"])
        missing = bm_ids - vec_ids
        extra = vec_ids - bm_ids
        if missing or extra:
            raise RuntimeError(f"BM25/Chroma không cùng Article corpus: BM25-only={len(missing)} Vector-only={len(extra)}; ví dụ={list(sorted(missing))[:5]}")
    results = evaluator.run_benchmark(queries=queries, methods=methods, top_k=args.top_k)

    print_comparison_table(results)

    csv_p, json_p, md_p = export_evaluation_results(
        results=results,
        validation_report=val_report,
        output_dir=output_dir,
        top_k=args.top_k,
    )

    print(f">> Xuất báo cáo chi tiết thành công:")
    print(f"   - File CSV : {csv_p}")
    print(f"   - File JSON: {json_p}")
    print(f"   - File MD  : {md_p}")


if __name__ == "__main__":
    main()
