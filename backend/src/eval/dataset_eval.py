"""
dataset_eval.py
Module quản lý, kiểm tra tính hợp lệ và chuẩn hóa dataset cho Retrieval Evaluation.

Nhiệm vụ:
- Hỗ trợ tải dataset Zalo AI BLDS (zalo_blds_scope.json) và benchmark queries (benchmark_queries.json).
- Kiểm tra tính toàn vẹn (schema, duplicates, missing fields).
- Đối chiếu ground_truth_node_ids với kho Knowledge Graph (nodes.json / Neo4j).
- Giữ nguyên nhãn gốc, không tự ý lọc bỏ câu hỏi khó, phân loại theo hop_type.
"""

from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class EvalQuery:
    """Cấu trúc dữ liệu chuẩn hóa cho một câu hỏi đánh giá Retrieval."""

    query_id: str
    question: str
    ground_truth_node_ids: List[str]
    hop_type: str = "SINGLE_HOP"
    source_dataset: str = "Unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "question": self.question,
            "ground_truth_node_ids": self.ground_truth_node_ids,
            "hop_type": self.hop_type,
            "source_dataset": self.source_dataset,
            "metadata": self.metadata,
        }


class EvaluationDatasetLoader:
    """Bộ nạp và kiểm định dataset phục vụ đánh giá Retrieval."""

    def __init__(self, kg_nodes_path: Optional[Path] = None):
        """Khởi tạo loader.

        Args:
            kg_nodes_path: Đường dẫn tới nodes.json để đối soát ID thực tế.
        """
        if kg_nodes_path is None:
            backend_dir = Path(__file__).resolve().parents[2]
            kg_nodes_path = backend_dir / "data" / "processed" / "nodes.json"

        self.kg_nodes_path = Path(kg_nodes_path)
        self.known_article_ids: Set[str] = set()
        self.known_all_node_ids: Set[str] = set()
        self._load_kg_nodes()

    def _load_kg_nodes(self) -> None:
        """Nạp danh sách node IDs từ Knowledge Graph để kiểm tra tính hợp lệ."""
        if not self.kg_nodes_path.exists():
            logger.warning(
                "Không tìm thấy file KG nodes tại: %s. Bỏ qua bước đối soát KG.",
                self.kg_nodes_path,
            )
            return

        try:
            with open(self.kg_nodes_path, "r", encoding="utf-8") as f:
                nodes_data = json.load(f)

            for n in nodes_data:
                nid = n.get("node_id")
                if not nid:
                    continue
                self.known_all_node_ids.add(nid)
                ntype = n.get("type") or n.get("label")
                if ntype == "Article":
                    self.known_article_ids.add(nid)

            logger.info(
                "Đã nạp đối soát KG: %d nodes tổng, trong đó %d Article nodes.",
                len(self.known_all_node_ids),
                len(self.known_article_ids),
            )
        except Exception as e:
            logger.error("Lỗi khi đọc file KG nodes: %s", e)

    def load_dataset(
        self, dataset_path: Path
    ) -> Tuple[List[EvalQuery], Dict[str, Any]]:
        """Nạp và chuẩn hóa dataset từ file JSON.

        Hỗ trợ cả 2 định dạng:
        - zalo_blds_scope.json: list of {query_id, question, ground_truth_node_ids, hop_type, ...}
        - benchmark_queries.json: {queries: [{id, query, expected_ids, ...}]} hoặc list of {id, query, ...}

        Args:
            dataset_path: Đường dẫn tới file JSON dataset.

        Returns:
            Tuple gồm:
            - Danh sách các EvalQuery đã chuẩn hóa.
            - Báo cáo kiểm định dữ liệu (validation_report).
        """
        path = Path(dataset_path)
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy file dataset: {path}")

        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        raw_list: List[Dict[str, Any]] = []
        if isinstance(raw_data, list):
            raw_list = raw_data
        elif isinstance(raw_data, dict) and "queries" in raw_data:
            raw_list = raw_data["queries"]
        else:
            raise ValueError(f"Định dạng dataset không hỗ trợ trong file: {path}")

        queries: List[EvalQuery] = []
        seen_query_ids: Set[str] = set()
        seen_questions: Set[str] = set()

        duplicate_id_count = 0
        duplicate_question_count = 0
        missing_ground_truth_count = 0
        empty_question_count = 0
        duplicate_gt_count = 0
        non_article_gt_nodes: Dict[str, List[str]] = {}
        unmatched_kg_nodes: Dict[str, List[str]] = {}
        hop_type_counts: Dict[str, int] = {}

        for item in raw_list:
            # 1. Trích xuất query_id
            qid = str(
                item.get("query_id") or item.get("id") or f"Q_{len(queries)+1}"
            ).strip()
            if qid in seen_query_ids:
                duplicate_id_count += 1
                logger.warning("Trùng query_id: %s", qid)
            seen_query_ids.add(qid)

            # 2. Trích xuất question text
            qtext = str(
                item.get("question") or item.get("query") or ""
            ).strip()
            if not qtext:
                empty_question_count += 1
                logger.warning("Query rỗng tại id: %s", qid)
                continue

            if qtext in seen_questions:
                duplicate_question_count += 1
            seen_questions.add(qtext)

            # 3. Trích xuất ground truth node IDs
            gt_ids: List[str] = []
            raw_gt = item.get("ground_truth_node_ids") or item.get("expected_ids") or []
            if isinstance(raw_gt, list):
                gt_ids = [str(x).strip() for x in raw_gt if str(x).strip()]
            elif isinstance(raw_gt, str) and raw_gt.strip():
                gt_ids = [raw_gt.strip()]

            if len(gt_ids) != len(set(gt_ids)):
                duplicate_gt_count += 1
            if not gt_ids:
                missing_ground_truth_count += 1
                logger.warning("Query %s không có ground truth", qid)

            # Đối chiếu với KG
            if self.known_all_node_ids:
                for target_id in gt_ids:
                    if target_id not in self.known_all_node_ids:
                        unmatched_kg_nodes.setdefault(target_id, []).append(qid)
                    elif target_id not in self.known_article_ids:
                        non_article_gt_nodes.setdefault(target_id, []).append(qid)

            # 4. Xác định hop_type
            hop_type = item.get("hop_type")
            if not hop_type:
                # Tự suy luận nếu dataset cũ không có hop_type
                if len(gt_ids) > 1:
                    docs = {gid.split("_D")[0] for gid in gt_ids if "_D" in gid}
                    if len(docs) > 1:
                        hop_type = "MULTI_HOP_CROSS_DOC"
                    else:
                        hop_type = "MULTI_HOP_INTRA_BLDS"
                else:
                    hop_type = "SINGLE_HOP"

            hop_type_counts[hop_type] = hop_type_counts.get(hop_type, 0) + 1

            source_dataset = item.get("source_dataset") or path.stem

            meta = {
                k: v
                for k, v in item.items()
                if k not in {"query_id", "id", "question", "query", "ground_truth_node_ids", "expected_ids", "hop_type", "source_dataset"}
            }

            queries.append(
                EvalQuery(
                    query_id=qid,
                    question=qtext,
                    ground_truth_node_ids=gt_ids,
                    hop_type=hop_type,
                    source_dataset=source_dataset,
                    metadata=meta,
                )
            )

        report = {
            "dataset_file": str(path.name),
            "total_queries": len(queries),
            "unique_query_ids": len(seen_query_ids),
            "unique_questions": len(seen_questions),
            "duplicate_id_count": duplicate_id_count,
            "duplicate_question_count": duplicate_question_count,
            "missing_ground_truth_count": missing_ground_truth_count,
            "empty_question_count": empty_question_count,
            "duplicate_gt_count": duplicate_gt_count,
            "non_article_gt_nodes": non_article_gt_nodes,
            "kg_validation_available": bool(self.known_all_node_ids),
            "hop_type_distribution": hop_type_counts,
            "unmatched_kg_nodes": unmatched_kg_nodes,
            "is_valid": (len(queries) > 0 and missing_ground_truth_count == 0
                         and empty_question_count == 0 and duplicate_id_count == 0
                         and duplicate_question_count == 0 and duplicate_gt_count == 0
                         and not unmatched_kg_nodes and not non_article_gt_nodes
                         and bool(self.known_all_node_ids)),
        }

        return queries, report

