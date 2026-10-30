"""
metrics_eval.py
Module tính toán và tổng hợp các chỉ số đánh giá chất lượng truy xuất (Retrieval Metrics).

Các chỉ số hỗ trợ:
- Hit@1, Hit@5, Hit@10
- Recall@1, Recall@5, Recall@10
- MRR@10 (Mean Reciprocal Rank)
- NDCG@10 (Normalized Discounted Cumulative Gain)
- Latency (ms): Mean, Median, Min, Max, P95
- Thống kê tổng hợp (Overall) và phân rã theo nhóm độ khó (hop_type).
"""

from collections import defaultdict
import math
import statistics
from typing import Any, Dict, List, Optional, Set


def compute_hit_at_k(retrieved_ids: List[str], ground_truth_set: Set[str], k: int) -> int:
    """Tính Hit@K: 1 nếu có ít nhất 1 node đúng trong top-k, ngược lại 0."""
    top_k = retrieved_ids[:k]
    return 1 if any(nid in ground_truth_set for nid in top_k) else 0


def compute_recall_at_k(retrieved_ids: List[str], ground_truth_set: Set[str], k: int) -> float:
    """Tính Recall@K: tỷ lệ các node đúng được tìm thấy trong top-k trên tổng số node đúng."""
    if not ground_truth_set:
        return 0.0
    top_k_set = set(retrieved_ids[:k])
    intersect = top_k_set.intersection(ground_truth_set)
    return len(intersect) / len(ground_truth_set)


def compute_mrr_at_k(retrieved_ids: List[str], ground_truth_set: Set[str], k: int = 10) -> float:
    """Tính Reciprocal Rank trong top-k: 1 / rank của node đúng đầu tiên."""
    if not ground_truth_set:
        return 0.0
    for rank, nid in enumerate(retrieved_ids[:k], start=1):
        if nid in ground_truth_set:
            return 1.0 / rank
    return 0.0


def compute_ndcg_at_k(retrieved_ids: List[str], ground_truth_set: Set[str], k: int = 10) -> float:
    """Tính NDCG@K với binary relevance."""
    if not ground_truth_set:
        return 0.0

    dcg = 0.0
    seen = set()
    for rank, nid in enumerate(retrieved_ids[:k], start=1):
        if nid in ground_truth_set and nid not in seen:
            seen.add(nid)
            dcg += 1.0 / math.log2(rank + 1)

    ideal_count = min(len(ground_truth_set), k)
    idcg = sum(1.0 / math.log2(r + 1) for r in range(1, ideal_count + 1))
    return dcg / idcg if idcg > 0 else 0.0


def evaluate_single_query(
    query_id: str,
    question: str,
    hop_type: str,
    retrieved_ids: List[str],
    ground_truth_ids: List[str],
    latency_ms: float,
    status: str = "SUCCESS",
    error_message: Optional[str] = None,
    scores: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """Tính toán toàn bộ metric cho một query cụ thể."""
    gt_set = set(ground_truth_ids)
    
    # Xác định vị trí hit đầu tiên
    first_hit_rank = None
    for rank, nid in enumerate(retrieved_ids, start=1):
        if nid in gt_set:
            first_hit_rank = rank
            break

    h1 = compute_hit_at_k(retrieved_ids, gt_set, k=1)
    h5 = compute_hit_at_k(retrieved_ids, gt_set, k=5)
    h10 = compute_hit_at_k(retrieved_ids, gt_set, k=10)

    r1 = compute_recall_at_k(retrieved_ids, gt_set, k=1)
    r5 = compute_recall_at_k(retrieved_ids, gt_set, k=5)
    r10 = compute_recall_at_k(retrieved_ids, gt_set, k=10)

    mrr10 = compute_mrr_at_k(retrieved_ids, gt_set, k=10)
    ndcg10 = compute_ndcg_at_k(retrieved_ids, gt_set, k=10)

    return {
        "query_id": query_id,
        "question": question,
        "hop_type": hop_type,
        "status": status,
        "error_message": error_message or "",
        "ground_truth_ids": ground_truth_ids,
        "predicted_ids": retrieved_ids,
        "scores": scores or [],
        "first_hit_rank": first_hit_rank,
        "hit@1": h1,
        "hit@5": h5,
        "hit@10": h10,
        "recall@1": round(r1, 4),
        "recall@5": round(r5, 4),
        "recall@10": round(r10, 4),
        "mrr@10": round(mrr10, 4),
        "ndcg@10": round(ndcg10, 4),
        "latency_ms": round(latency_ms, 2),
    }


def aggregate_query_metrics(query_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Tổng hợp chỉ số thống kê từ danh sách kết quả từng câu."""
    n = len(query_records)
    if n == 0:
        return {
            "total_queries": 0,
            "hit@1": 0.0,
            "hit@5": 0.0,
            "hit@10": 0.0,
            "recall@1": 0.0,
            "recall@5": 0.0,
            "recall@10": 0.0,
            "mrr@10": 0.0,
            "ndcg@10": 0.0,
            "avg_latency_ms": 0.0,
            "median_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "success_count": 0,
            "no_results_count": 0,
            "error_count": 0,
        }

    success_count = sum(1 for q in query_records if q.get("status") == "SUCCESS")
    no_results_count = sum(1 for q in query_records if q.get("status") == "NO_RESULTS")
    error_count = sum(1 for q in query_records if q.get("status") == "ERROR")

    hit_1 = sum(q.get("hit@1", 0) for q in query_records) / n
    hit_5 = sum(q.get("hit@5", 0) for q in query_records) / n
    hit_10 = sum(q.get("hit@10", 0) for q in query_records) / n

    rec_1 = sum(q.get("recall@1", 0.0) for q in query_records) / n
    rec_5 = sum(q.get("recall@5", 0.0) for q in query_records) / n
    rec_10 = sum(q.get("recall@10", 0.0) for q in query_records) / n

    mrr_10 = sum(q.get("mrr@10", 0.0) for q in query_records) / n
    ndcg_10 = sum(q.get("ndcg@10", 0.0) for q in query_records) / n

    # Thời gian lỗi không đại diện cho độ trễ truy xuất thành công.
    latencies = sorted(q.get("latency_ms", 0.0) for q in query_records if q.get("status") != "ERROR")
    if not latencies:
        latencies = [0.0]
    avg_lat = sum(latencies) / len(latencies)
    med_lat = statistics.median(latencies)
    p95_position = 0.95 * (n - 1)
    lower = int(math.floor(p95_position))
    upper = int(math.ceil(p95_position))
    p95_lat = latencies[lower] + (p95_position - lower) * (latencies[upper] - latencies[lower])

    return {
        "total_queries": n,
        "success_count": success_count,
        "no_results_count": no_results_count,
        "error_count": error_count,
        "hit@1": round(hit_1 * 100, 2),
        "hit@5": round(hit_5 * 100, 2),
        "hit@10": round(hit_10 * 100, 2),
        "recall@1": round(rec_1 * 100, 2),
        "recall@5": round(rec_5 * 100, 2),
        "recall@10": round(rec_10 * 100, 2),
        "mrr@10": round(mrr_10, 4),
        "ndcg@10": round(ndcg_10, 4),
        "avg_latency_ms": round(avg_lat, 2),
        "median_latency_ms": round(med_lat, 2),
        "p95_latency_ms": round(p95_lat, 2),
    }


def compute_evaluation_report(query_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Tạo báo cáo hoàn chỉnh gồm overall và breakdown theo từng hop_type."""
    overall = aggregate_query_metrics(query_records)

    by_hop = defaultdict(list)
    for q in query_records:
        ht = q.get("hop_type", "UNKNOWN")
        by_hop[ht].append(q)

    hop_breakdown = {}
    for ht, group in sorted(by_hop.items()):
        hop_breakdown[ht] = aggregate_query_metrics(group)

    return {
        "overall": overall,
        "by_hop_type": hop_breakdown,
        "queries": query_records,
    }

