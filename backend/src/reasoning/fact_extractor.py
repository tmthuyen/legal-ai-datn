"""Trích xuất và kiểm định facts từ câu hỏi tình huống pháp lý."""

import json
from pathlib import Path
from typing import Any, Mapping

from src.utils.logger import setup_logger

logger = setup_logger("fact_extractor", "fact_extractor.log")

FACT_EXTRACTION_TASK_ID = "LEGAL_FACT_EXTRACTION"
_CONDITION_OPERATORS = {"eq", "neq", "gt", "gte", "lt", "lte", "in", "not_in", "exists"}
_INPUT_EFFECTS = {"REQUIRE", "PROHIBIT"}


class FactExtractionError(ValueError):
    """Lỗi khi output facts không phù hợp với rule hoặc predicate catalog."""


class FactExtractor:
    """Tạo prompt và kiểm định facts theo predicate của một legal rule."""

    def __init__(
        self,
        model: Any = None,
        predicates_catalog: Mapping[str, Mapping[str, Any]] | None = None,
        task_id: str = FACT_EXTRACTION_TASK_ID,
    ) -> None:
        """Khởi tạo fact extractor.

        Args:
            model: Model có phương thức ``predict(task_id, input_text)``. Có thể
                để ``None`` khi chỉ cần tạo prompt hoặc kiểm định output.
            predicates_catalog: Catalog predicate; nếu bỏ qua sẽ đọc catalog chuẩn.
            task_id: Mã task JSON đã đăng ký trong legal model.
        """
        self.model = model
        self.predicates_catalog = dict(
            predicates_catalog or self._load_default_predicates_catalog()
        )
        self.task_id = task_id

    @staticmethod
    def _load_default_predicates_catalog() -> dict[str, Mapping[str, Any]]:
        """Đọc catalog predicate mặc định của backend."""
        catalog_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "rules"
            / "catalogs"
            / "predicates.json"
        )
        with catalog_path.open("r", encoding="utf-8") as file:
            return json.load(file)["predicates"]

    def collect_rule_predicates(self, rule: Mapping[str, Any]) -> list[str]:
        """Thu thập predicate đầu vào cần trích xuất cho rule.

        Chỉ lấy điều kiện ``when``, ``unless`` và các effect ``REQUIRE``/
        ``PROHIBIT``. Các predicate được sinh ra bởi ``DERIVE``, ``PERMIT``
        hoặc ``DENY_RECOGNITION`` không phải fact đầu vào.
        """
        predicates: list[str] = []

        def add(predicate: Any) -> None:
            if isinstance(predicate, str) and predicate not in predicates:
                predicates.append(predicate)

        def visit_condition(expression: Any) -> None:
            if isinstance(expression, list) and len(expression) == 3:
                add(expression[0])
                return
            if isinstance(expression, dict):
                for child in expression.values():
                    if isinstance(child, list):
                        for item in child:
                            visit_condition(item)
                    else:
                        visit_condition(child)

        visit_condition(rule.get("when"))
        for exception in rule.get("unless", []):
            visit_condition(exception)
        for item in rule.get("then", []):
            if item.get("effect") in _INPUT_EFFECTS:
                add(item.get("predicate"))
        return predicates

    def build_prompt(self, question: str, rule: Mapping[str, Any]) -> str:
        """Tạo prompt trích xuất facts theo rule và catalog."""
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question phải là chuỗi không rỗng.")

        predicate_names = self.collect_rule_predicates(rule)
        predicate_specs = {
            name: self.predicates_catalog[name]
            for name in predicate_names
            if name in self.predicates_catalog
        }
        unknown_predicates = [
            name for name in predicate_names if name not in self.predicates_catalog
        ]
        if unknown_predicates:
            raise FactExtractionError(
                f"Predicate chưa có trong catalog: {unknown_predicates}"
            )

        schema = {
            "facts": {name: "<value theo type/enum>" for name in predicate_names},
            "missing_facts": ["<predicate chưa xác định>"],
            "evidence": {name: "<trích dẫn ngắn từ input>" for name in predicate_names},
        }
        return (
            f"Rule đang xét: {rule.get('id', '<unknown>')}\n"
            "Chỉ trích xuất dữ kiện thực tế. Không tự suy diễn kết luận pháp lý hay đánh giá đúng/sai.\n"
            "Danh sách predicate được phép và mô tả:\n"
            f"{json.dumps(predicate_specs, ensure_ascii=False, indent=2)}\n\n"
            "Schema JSON bắt buộc:\n"
            f"{json.dumps(schema, ensure_ascii=False, indent=2)}\n\n"
            f"Tình huống cần phân tích:\n{question.strip()}"
        )

    def extract(self, question: str, rule: Mapping[str, Any]) -> dict[str, Any]:
        """Gọi model, parse và kiểm định facts theo rule."""
        if self.model is None:
            raise FactExtractionError("FactExtractor chưa được cung cấp model.")

        prompt = self.build_prompt(question, rule)
        response = self.model.predict(self.task_id, prompt)
        output = self._unwrap_model_output(response)
        result = self.validate_output(output, rule)
        result["prompt"] = prompt
        return result

    def validate_output(
        self, output: Any, rule: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Kiểm tra output facts về predicate, kiểu dữ liệu và enum."""
        if not isinstance(output, dict):
            raise FactExtractionError("Output fact phải là một object JSON.")

        required_predicates = self.collect_rule_predicates(rule)
        facts = output.get("facts")
        if not isinstance(facts, dict):
            raise FactExtractionError("Output phải có trường facts dạng object.")

        errors: list[str] = []
        normalized_facts: dict[str, Any] = {}
        for predicate, value in facts.items():
            if predicate not in required_predicates:
                errors.append(f"Predicate không thuộc rule: {predicate}")
                continue
            if value is None:
                continue
            errors.extend(self._validate_value(predicate, value))
            if not errors or predicate not in normalized_facts:
                normalized_facts[predicate] = value

        missing = output.get("missing_facts", [])
        if not isinstance(missing, list) or any(
            item not in required_predicates for item in missing
        ):
            errors.append("missing_facts phải là danh sách predicate thuộc rule.")
            missing = []

        for predicate in required_predicates:
            if predicate not in normalized_facts and predicate not in missing:
                missing.append(predicate)

        evidence = output.get("evidence", {})
        if not isinstance(evidence, dict):
            errors.append("evidence phải là object.")
            evidence = {}
        evidence = {
            key: value
            for key, value in evidence.items()
            if key in normalized_facts and isinstance(value, str)
        }

        if errors:
            raise FactExtractionError("; ".join(dict.fromkeys(errors)))

        return {
            "facts": normalized_facts,
            "missing_facts": [
                predicate for predicate in required_predicates if predicate in missing
            ],
            "evidence": evidence,
        }

    def _validate_value(self, predicate: str, value: Any) -> list[str]:
        """Kiểm tra một giá trị theo định nghĩa predicate."""
        spec = self.predicates_catalog[predicate]
        expected_type = spec.get("type")
        errors: list[str] = []
        if expected_type == "boolean" and type(value) is not bool:
            errors.append(f"{predicate} phải có kiểu boolean.")
        elif expected_type == "integer" and (type(value) is not int):
            errors.append(f"{predicate} phải có kiểu integer.")
        elif expected_type == "number" and (
            not isinstance(value, (int, float)) or isinstance(value, bool)
        ):
            errors.append(f"{predicate} phải có kiểu number.")
        elif expected_type == "string" and not isinstance(value, str):
            errors.append(f"{predicate} phải có kiểu string.")
        elif expected_type == "enum" and value not in spec.get("allowed_values", []):
            errors.append(
                f"{predicate} phải thuộc enum {spec.get('allowed_values', [])}."
            )
        return errors

    @staticmethod
    def _unwrap_model_output(response: Any) -> Any:
        """Lấy JSON output từ response chuẩn của LegalReasoningModel hoặc chuỗi raw."""
        output = response
        if isinstance(response, dict) and "result" in response:
            output = response["result"].get("output")
        if isinstance(output, str):
            cleaned = output.strip()
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if len(lines) >= 2 and lines[-1].strip().startswith("```"):
                    cleaned = "\n".join(lines[1:-1]).strip()
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end >= start:
                cleaned = cleaned[start : end + 1]
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as error:
                raise FactExtractionError("Model trả về JSON không hợp lệ.") from error
        return output
