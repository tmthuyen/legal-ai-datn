"""
eval package
Cung cấp các công cụ kiểm định dataset, đo lường chỉ số (metrics)
và thực thi benchmark đánh giá hiệu năng truy xuất thông tin (Retrieval Evaluation).
"""

from src.eval.dataset_eval import EvalQuery, EvaluationDatasetLoader
from src.eval.metrics_eval import (
    aggregate_query_metrics,
    compute_evaluation_report,
    compute_hit_at_k,
    compute_mrr_at_k,
    compute_ndcg_at_k,
    compute_recall_at_k,
    evaluate_single_query,
)

__all__ = [
    "EvalQuery",
    "EvaluationDatasetLoader",
    "compute_hit_at_k",
    "compute_recall_at_k",
    "compute_mrr_at_k",
    "compute_ndcg_at_k",
    "evaluate_single_query",
    "aggregate_query_metrics",
    "compute_evaluation_report",
]
