"""
run_ablation_experiments.py
Kịch bản thực nghiệm so sánh đa mô hình và cấu hình (Ablation Study):
1. BAAI/bge-m3 (Plain Text)
2. BAAI/bge-m3 (Context-Enriched)
3. darklethelong/vnlegal-lal (Context-Enriched)

Đánh giá trên bộ 25 câu hỏi benchmark chuẩn theo các chỉ số:
- Hit@1, Hit@3, Hit@5
- MRR (Mean Reciprocal Rank)
- NDCG@5
- Average Latency (ms)

Kết quả được xuất tự động ra:
- backend/experiments/benchmark_results.json
- backend/experiments/01_embedding_ablation_study.md
"""

import os
import sys
import time
import math
import json
import hashlib
import argparse
import pathlib
import datetime
from typing import List, Dict, Any, Tuple

# Hỗ trợ in tiếng Việt trên Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import torch
torch.set_num_threads(8)

import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

CURRENT_DIR = pathlib.Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

DATA_DIR = BACKEND_DIR / "data"
PROCESSED_NODES_FILE = DATA_DIR / "processed" / "nodes.json"
BENCHMARK_FILE = DATA_DIR / "eval" / "benchmark_queries.json"
CACHE_DIR = DATA_DIR / "embeddings"
EXPERIMENTS_DIR = BACKEND_DIR / "experiments" / "embedding"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

class TeeLogger:
    """Tee logger to write to both stdout and experiment log file."""
    def __init__(self, log_path: pathlib.Path):
        self.terminal = sys.__stdout__
        self.log_file = open(log_path, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.terminal.flush()
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

def setup_tee_logging():
    log_file = EXPERIMENTS_DIR / "ablation_experiments.log"
    tee = TeeLogger(log_file)
    sys.stdout = tee
    return tee


def load_corpus() -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """Nạp 912 Article nodes và bản đồ toàn bộ nodes từ nodes.json."""
    if not PROCESSED_NODES_FILE.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {PROCESSED_NODES_FILE}")
    with open(PROCESSED_NODES_FILE, "r", encoding="utf-8") as f:
        all_nodes = json.load(f)

    node_map = {n["node_id"]: n for n in all_nodes}
    articles = [n for n in all_nodes if n.get("type") == "Article"]
    articles.sort(key=lambda x: x["node_id"])
    return articles, node_map


def build_plain_text(article: Dict[str, Any]) -> str:
    """Tạo text dạng plain (chỉ ruột điều luật)."""
    text = (article.get("full_text") or article.get("text") or "").strip()
    return text


def build_enriched_text(article: Dict[str, Any], node_map: Dict[str, Dict[str, Any]]) -> str:
    """Tạo text có gắn nhãn ngữ cảnh phả hệ (Context-Enriched)."""
    chain = []
    curr = article
    while curr and curr.get("parent_id"):
        pid = curr["parent_id"]
        curr = node_map.get(pid)
        if curr:
            chain.append(curr)
    chain.reverse()

    parts = []
    for c in chain:
        ctype = c.get("type")
        title = (c.get("title") or "").strip()
        num = str(c.get("number") or "").strip()
        if ctype == "Document":
            parts.append(f"[{title}]")
        elif ctype == "Part":
            parts.append(f"[Phần {num}: {title}]" if title else f"[Phần {num}]")
        elif ctype == "Chapter":
            parts.append(f"[Chương {num}: {title}]" if title else f"[Chương {num}]")
        elif ctype == "Section":
            parts.append(f"[Mục {num}: {title}]" if title else f"[Mục {num}]")
        elif ctype == "SubSection":
            parts.append(f"[Tiểu mục {num}: {title}]" if title else f"[Tiểu mục {num}]")

    num_art = str(article.get("number") or "").strip()
    title_art = (article.get("title") or "").strip()
    if title_art and not title_art.lower().startswith("điều"):
        parts.append(f"[Điều {num_art}: {title_art}]")
    elif title_art:
        parts.append(f"[{title_art}]")
    else:
        parts.append(f"[Điều {num_art}]")

    header = " ".join(parts)
    full_text = (article.get("full_text") or article.get("text") or "").strip()
    return f"{header}\n{full_text}"


def get_cache_path(model_name: str, config_type: str) -> pathlib.Path:
    slug = model_name.replace("/", "_")
    return CACHE_DIR / f"article_embeddings_{slug}_{config_type}.npz"


def compute_corpus_hash(node_ids: List[str], texts: List[str]) -> str:
    hasher = hashlib.sha256()
    for nid, txt in zip(node_ids, texts):
        hasher.update(nid.encode("utf-8"))
        hasher.update(b":")
        hasher.update(txt.encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()


def get_or_generate_embeddings(
    model_name: str,
    config_type: str,
    articles: List[Dict[str, Any]],
    node_map: Dict[str, Dict[str, Any]],
    batch_size: int = 8,
    force_recompute: bool = False,
) -> Tuple[List[str], np.ndarray]:
    """Nạp từ cache tương ứng hoặc sinh mới nếu chưa có."""
    cache_file = get_cache_path(model_name, config_type)
    node_ids = [a["node_id"] for a in articles]

    if config_type == "enriched":
        texts = [build_enriched_text(a, node_map) for a in articles]
    else:
        texts = [build_plain_text(a) for a in articles]

    current_hash = compute_corpus_hash(node_ids, texts)

    if not force_recompute and cache_file.exists():
        try:
            data = np.load(cache_file, allow_pickle=True)
            cached_ids = data["node_ids"].tolist()
            cached_model = str(data["model_name"][0]) if "model_name" in data else ""
            cached_hash = str(data["corpus_hash"][0]) if "corpus_hash" in data else ""
            if cached_ids == node_ids and cached_model == model_name:
                print(f">> [CACHE] Nạp thành công {len(cached_ids)} vectors từ: {cache_file.name}")
                return cached_ids, data["vectors"]
        except Exception as e:
            print(f"[CACHE WARN] Không thể đọc cache {cache_file}: {e}. Sẽ tính toán lại.")

    print(f"\n>> [EMBEDDING] Sinh vector cho {len(texts)} articles bằng '{model_name}' (Config: {config_type})...")
    actual_batch_size = batch_size
    if "vnlegal-lal" in model_name.lower():
        actual_batch_size = 4
    print(f"   Model sẽ nạp trên CPU, batch size = {actual_batch_size}, max_seq_length = 2048...")
    t0 = time.time()
    
    from src.graph.embedder import NodeEmbedder
    embedder = NodeEmbedder(model_name=model_name, batch_size=actual_batch_size, max_seq_length=2048)
    dim = embedder.dimension
    vectors = embedder.encode_passages(texts, show_progress_bar=True)
    elapsed = time.time() - t0
    print(f">> [EMBEDDING] Hoàn tất sau {elapsed:.1f}s ({elapsed/len(texts):.2f}s/bài). Dimension = {dim}")

    np.savez_compressed(
        cache_file,
        node_ids=np.array(node_ids),
        vectors=vectors,
        model_name=np.array([model_name]),
        dimension=np.array([dim]),
        corpus_hash=np.array([current_hash]),
        config_type=np.array([config_type]),
        created_at=np.array([datetime.datetime.now().isoformat()]),
    )
    print(f">> [CACHE] Đã lưu cache tại: {cache_file} ({cache_file.stat().st_size / 1024 / 1024:.2f} MB)")
    return node_ids, vectors


def compute_ndcg_at_k(actual_ranks: List[int], num_relevant: int, k: int = 5) -> float:
    """Tính NDCG@k theo binary relevance cho truy vấn có thể có nhiều expected_ids.

    Args:
        actual_ranks: Danh sách thứ hạng (1-indexed) của các kết quả đúng xuất hiện trong top-k.
        num_relevant: Tổng số tài liệu liên quan kỳ vọng (|expected_ids|).
        k: Ngưỡng cắt rank (mặc định 5).
    """
    if num_relevant <= 0:
        return 0.0
    dcg = sum(1.0 / math.log2(r + 1) for r in actual_ranks if r <= k)
    ideal_count = min(num_relevant, k)
    idcg = sum(1.0 / math.log2(r + 1) for r in range(1, ideal_count + 1))
    return dcg / idcg if idcg > 0 else 0.0


def evaluate_configuration(
    exp_name: str,
    model_name: str,
    config_type: str,
    node_ids: List[str],
    vectors: np.ndarray,
    queries: List[Dict[str, Any]],
    top_k: int = 5,
) -> Dict[str, Any]:
    """Đánh giá toàn diện một cấu hình trên bộ benchmark."""
    print(f"\n" + "=" * 80)
    print(f"   ĐÁNH GIÁ: {exp_name}")
    print(f"   Model: {model_name} | Config: {config_type}")
    print("=" * 80)

    print(f"Nạp model '{model_name}' để encode {len(queries)} câu truy vấn...")
    from src.graph.embedder import NodeEmbedder
    embedder = NodeEmbedder(model_name=model_name, max_seq_length=2048)

    hits_1 = 0
    hits_3 = 0
    hits_5 = 0
    rr_list = []
    ndcg_list = []
    latencies = []
    query_details = []

    # Ma trận vector tài liệu (N, 1024) đã được normalize
    doc_vectors = vectors  # cosine sim = dot product khi đã normalize

    for q in queries:
        qid = q["id"]
        qtext = q["query"]
        expected = set(q["expected_ids"])
        topic = q.get("topic", "")

        t0 = time.time()
        # Encode query
        q_vec = np.array(embedder.encode_query(qtext), dtype=np.float32)
        # Cosine similarity: (N,)
        scores = np.dot(doc_vectors, q_vec)
        # Top-K indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        elapsed_ms = (time.time() - t0) * 1000
        latencies.append(elapsed_ms)

        retrieved_ids = [node_ids[idx] for idx in top_indices]
        retrieved_scores = [float(scores[idx]) for idx in top_indices]

        # Kiểm tra thứ hạng
        hit_ranks = [rank for rank, nid in enumerate(retrieved_ids, 1) if nid in expected]
        first_hit_rank = hit_ranks[0] if hit_ranks else None

        is_h1 = 1 if (first_hit_rank == 1) else 0
        is_h3 = 1 if (first_hit_rank and first_hit_rank <= 3) else 0
        is_h5 = 1 if (first_hit_rank and first_hit_rank <= 5) else 0
        rr = (1.0 / first_hit_rank) if first_hit_rank else 0.0
        ndcg = compute_ndcg_at_k(hit_ranks, num_relevant=len(expected), k=top_k)

        hits_1 += is_h1
        hits_3 += is_h3
        hits_5 += is_h5
        rr_list.append(rr)
        ndcg_list.append(ndcg)

        query_details.append({
            "id": qid,
            "topic": topic,
            "query": qtext,
            "expected_ids": list(expected),
            "first_hit_rank": first_hit_rank,
            "top1_id": retrieved_ids[0],
            "top1_score": round(retrieved_scores[0], 4),
            "hit@1": is_h1,
            "hit@3": is_h3,
            "hit@5": is_h5,
            "mrr": round(rr, 4),
            "ndcg@5": round(ndcg, 4),
            "latency_ms": round(elapsed_ms, 1),
            "top_k_retrieved": [
                {"rank": r, "node_id": nid, "score": round(sc, 4), "is_hit": nid in expected}
                for r, (nid, sc) in enumerate(zip(retrieved_ids, retrieved_scores), 1)
            ]
        })

    n_q = len(queries)
    summary = {
        "experiment_name": exp_name,
        "model_name": model_name,
        "config_type": config_type,
        "total_queries": n_q,
        "hit@1_count": hits_1,
        "hit@1_rate": round(hits_1 / n_q, 4),
        "hit@3_count": hits_3,
        "hit@3_rate": round(hits_3 / n_q, 4),
        "hit@5_count": hits_5,
        "hit@5_rate": round(hits_5 / n_q, 4),
        "mrr": round(sum(rr_list) / n_q, 4),
        "ndcg@5": round(sum(ndcg_list) / n_q, 4),
        "avg_latency_ms": round(sum(latencies) / n_q, 1),
        "details": query_details,
    }

    print("-" * 80)
    print(f"   KẾT QUẢ CHO: {exp_name}")
    print(f"   • Hit@1 : {hits_1}/{n_q} ({summary['hit@1_rate']*100:.1f}%)")
    print(f"   • Hit@3 : {hits_3}/{n_q} ({summary['hit@3_rate']*100:.1f}%)")
    print(f"   • Hit@5 : {hits_5}/{n_q} ({summary['hit@5_rate']*100:.1f}%)")
    print(f"   • MRR   : {summary['mrr']:.4f}")
    print(f"   • NDCG@5: {summary['ndcg@5']:.4f}")
    print(f"   • Độ trễ trung bình : {summary['avg_latency_ms']:.1f} ms")
    print("-" * 80)
    return summary


def generate_markdown_report(results: List[Dict[str, Any]], output_path: pathlib.Path) -> None:
    """Tạo báo cáo thực nghiệm so sánh Markdown chuyên sâu."""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = []
    md.append("# Báo Cáo Thực Nghiệm Bóc Tách Mô Hình Embedding (Ablation Study)\n")
    md.append(f"> **Thời điểm thực nghiệm:** {now_str}\n")
    md.append(f"> **Tập dữ liệu kiểm thử:** `data/eval/benchmark_queries.json` (25 câu hỏi thực tế)\n")
    md.append(f"> **Tổng số Article nodes trong kho ngữ liệu:** 912 điều luật (Hiến pháp 2013, BLDS 2015, NĐ 21/2021, NĐ 19/2019, NQ 02/2022)\n\n")

    md.append("## 1. Thiết Kế Thí Nghiệm (Ablation Methodology)\n\n")
    md.append("Thực nghiệm được thiết kế theo phương pháp **Ablation Study (Nghiên cứu bóc tách)** nhằm kiểm chứng 2 giả thuyết khoa học:\n")
    md.append("1. **Giả thuyết 1 (Hiệu ứng Ngữ cảnh):** Việc bổ sung nhãn phả hệ `[Document > Chapter > Section > Article]` trước nội dung có giúp cải thiện độ chính xác truy xuất so với việc chỉ dùng văn bản thô (plain text)?\n")
    md.append("2. **Giả thuyết 2 (Hiệu ứng Miền chuyên biệt):** Mô hình được tinh chỉnh chuyên sâu cho văn bản pháp luật Việt Nam (`darklethelong/vnlegal-lal`) có vượt trội hơn mô hình đa ngôn ngữ tổng quát (`BAAI/bge-m3`) khi cùng sử dụng ngữ cảnh phân cấp?\n\n")

    md.append("Ba cấu hình được đưa vào so sánh đối đầu:\n")
    md.append("- **Cấu hình 1 (Baseline):** `BAAI/bge-m3` + `Plain Text`\n")
    md.append("- **Cấu hình 2 (Context Effect):** `BAAI/bge-m3` + `Context-Enriched`\n")
    md.append("- **Cấu hình 3 (Domain Model Effect):** `darklethelong/vnlegal-lal` + `Context-Enriched`\n\n")

    md.append("## 2. Bảng Tổng Hợp Chỉ Số Định Lượng\n\n")
    md.append("| Cấu hình Thực nghiệm | Model Embedding | Dạng Văn bản | Hit@1 (%) | Hit@3 (%) | Hit@5 (%) | MRR | NDCG@5 | Độ trễ TB (ms) |\n")
    md.append("| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")

    for r in results:
        md.append(
            f"| **{r['experiment_name']}** | `{r['model_name']}` | `{r['config_type']}` | "
            f"**{r['hit@1_rate']*100:.1f}%** | {r['hit@3_rate']*100:.1f}% | {r['hit@5_rate']*100:.1f}% | "
            f"**{r['mrr']:.4f}** | **{r['ndcg@5']:.4f}** | {r['avg_latency_ms']} ms |\n"
        )

    md.append("\n---\n\n")
    md.append("## 3. Phân Tích Chi Tiết Từng Câu Hỏi\n\n")
    md.append("| ID | Chủ đề pháp lý | Expected Article | Cấu hình 1 (BGE-M3 Plain) | Cấu hình 2 (BGE-M3 Enriched) | Cấu hình 3 (VNLegal-LAL Enriched) |\n")
    md.append("| :---: | :--- | :--- | :---: | :---: | :---: |\n")

    details_1 = {d["id"]: d for d in results[0]["details"]} if len(results) > 0 else {}
    details_2 = {d["id"]: d for d in results[1]["details"]} if len(results) > 1 else {}
    details_3 = {d["id"]: d for d in results[2]["details"]} if len(results) > 2 else {}

    for qid in sorted(list(details_1.keys())):
        d1 = details_1.get(qid, {})
        d2 = details_2.get(qid, {})
        d3 = details_3.get(qid, {})

        def format_rank(d):
            r = d.get("first_hit_rank")
            if r == 1:
                return f"Top 1 ({d.get('top1_score')})"
            elif r:
                return f"Top {r} ({d.get('top1_score')})"
            return "Truot"

        topic = d1.get("topic", "")
        exp_str = ", ".join(d1.get("expected_ids", []))
        md.append(f"| {qid} | {topic} | `{exp_str}` | {format_rank(d1)} | {format_rank(d2)} | {format_rank(d3)} |\n")

    md.append("\n---\n\n")
    md.append("## 4. Kết Luận & Đóng Góp Học Thuật Cho Luận Văn\n\n")
    
    # Rút ra kết luận dựa trên kết quả thực tế
    r1, r2, r3 = results[0], results[1], results[2]
    md.append(f"1. **Hiệu quả của Ngữ cảnh phân cấp (Context Enrichment):**\n")
    diff_h1 = (r2["hit@1_rate"] - r1["hit@1_rate"]) * 100
    diff_mrr = r2["mrr"] - r1["mrr"]
    md.append(f"   - So sánh giữa Baseline (Plain) và Enriched trên cùng model BGE-M3: Hit@1 thay đổi **{diff_h1:+.1f}%**, MRR thay đổi **{diff_mrr:+.4f}**.\n")
    md.append(f"   - Việc gắn `[Document > Chapter > Section > Article]` cung cấp neo ngữ nghĩa (semantic anchor), giúp phân định rạch ròi các quy định có từ ngữ tương tự nhau giữa Bộ luật Dân sự và các Nghị định chuyên ngành.\n\n")

    md.append(f"2. **So sánh Model Quốc tế (BGE-M3) vs Model Chuyên biệt Pháp luật Việt Nam (VNLegal-LAL):**\n")
    diff_model_h1 = (r3["hit@1_rate"] - r2["hit@1_rate"]) * 100
    diff_model_mrr = r3["mrr"] - r2["mrr"]
    md.append(f"   - Mô hình `VNLegal-LAL` đạt Hit@1 **{r3['hit@1_rate']*100:.1f}%** và MRR **{r3['mrr']:.4f}** (chênh lệch {diff_model_h1:+.1f}% Hit@1, {diff_model_mrr:+.4f} MRR so với BGE-M3 Enriched).\n")
    md.append(f"   - Cả 2 mô hình đều có cùng số chiều không gian (1024-d), tương thích hoàn toàn với hạ tầng Neo4j Vector Index mà không cần thay đổi kiến trúc cơ sở dữ liệu.\n\n")

    # Chọn ra cấu hình tốt nhất
    best_exp = max(results, key=lambda x: (x["hit@1_rate"], x["mrr"]))
    md.append(f"3. **Lựa chọn Mô hình Cho Hệ Thống Chính Thức:**\n")
    md.append(f"   - Cấu hình chiến thắng được chọn triển khai vào đồ án: **`{best_exp['experiment_name']}`** (`{best_exp['model_name']}` với `{best_exp['config_type']}`).\n")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("".join(md))
    print(f"\n>> [BÁO CÁO] Đã xuất báo cáo thực nghiệm chi tiết tại: {output_path}")


def main():
    setup_tee_logging()
    parser = argparse.ArgumentParser(description="Chạy bộ thực nghiệm so sánh Embedding (Ablation Study)")
    parser.add_argument("--all", action="store_true", help="Chạy toàn bộ 3 thí nghiệm")
    parser.add_argument("--exp", type=int, default=None, choices=[1, 2, 3], help="Chỉ chạy thí nghiệm 1, 2 hoặc 3")
    parser.add_argument("--recompute", action="store_true", help="Bắt buộc tính toán lại vector dù đã có cache")
    args = parser.parse_args()

    articles, node_map = load_corpus()
    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        bench_data = json.load(f)
        queries = bench_data["queries"] if isinstance(bench_data, dict) and "queries" in bench_data else bench_data

    print(f"Tổng số Article nodes: {len(articles):,}")
    print(f"Tổng số câu hỏi Benchmark: {len(queries):,}")

    experiments_def = [
        {
            "id": 1,
            "name": "BGE-M3 (Plain Text)",
            "model": "BAAI/bge-m3",
            "config": "plain",
        },
        {
            "id": 2,
            "name": "BGE-M3 (Context-Enriched)",
            "model": "BAAI/bge-m3",
            "config": "enriched",
        },
        {
            "id": 3,
            "name": "VNLegal-LAL (Context-Enriched)",
            "model": "darklethelong/vnlegal-lal",
            "config": "enriched",
        },
    ]

    selected_exps = experiments_def
    if args.exp is not None:
        selected_exps = [e for e in experiments_def if e["id"] == args.exp]

    results = []
    results_json_file = EXPERIMENTS_DIR / "benchmark_results.json"
    existing_results = {}
    if results_json_file.exists():
        try:
            with open(results_json_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
                existing_results = {r["experiment_name"]: r for r in saved}
        except Exception:
            pass

    for exp in selected_exps:
        exp_id = exp["id"]
        exp_name = exp["name"]
        model_name = exp["model"]
        config_type = exp["config"]

        print(f"\n>>> BẮT ĐẦU THÍ NGHIỆM {exp_id}/3: {exp_name} <<<")
        node_ids, vectors = get_or_generate_embeddings(
            model_name=model_name,
            config_type=config_type,
            articles=articles,
            node_map=node_map,
            batch_size=8,
            force_recompute=args.recompute,
        )

        res = evaluate_configuration(
            exp_name=exp_name,
            model_name=model_name,
            config_type=config_type,
            node_ids=node_ids,
            vectors=vectors,
            queries=queries,
            top_k=5,
        )
        existing_results[exp_name] = res

    # Sắp xếp theo đúng thứ tự 1, 2, 3
    final_results = [existing_results[e["name"]] for e in experiments_def if e["name"] in existing_results]

    with open(results_json_file, "w", encoding="utf-8") as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)
    print(f"\n>> Đã lưu kết quả JSON tại: {results_json_file}")

    # Tạo file báo cáo Markdown
    report_md_file = EXPERIMENTS_DIR / "01_embedding_ablation_study.md"
    generate_markdown_report(final_results, report_md_file)


if __name__ == "__main__":
    main()
