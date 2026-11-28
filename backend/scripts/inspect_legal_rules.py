r"""Đọc rule pháp lý và xuất dữ liệu node liên quan từ Neo4j.

Ví dụ PowerShell bên dưới chạy từ thư mục gốc repository. Mỗi ví dụ là độc lập.

1. Xuất toàn bộ rule, dùng file mặc định
   (backend\data\processed\rule_graph_context_all.json):

   $ErrorActionPreference = 'Stop'
   Set-Location backend
   $env:PYTHONIOENCODING = 'utf-8'
   $python = '.\.venv\Scripts\python.exe'
   & $python scripts\inspect_legal_rules.py --all
   if ($LASTEXITCODE -ne 0) { throw 'Xuất toàn bộ rule thất bại.' }

2. Xuất một rule, dùng file mặc định
   (backend\data\processed\rule_graph_context_single.json):

   $ErrorActionPreference = 'Stop'
   Set-Location backend
   $env:PYTHONIOENCODING = 'utf-8'
   $python = '.\.venv\Scripts\python.exe'
   & $python scripts\inspect_legal_rules.py --rule-id BLDS_D117_K1_01
   if ($LASTEXITCODE -ne 0) { throw 'Xuất rule thất bại.' }

3. Chọn thư mục rule và file đầu ra:

   $ErrorActionPreference = 'Stop'
   Set-Location backend
   $env:PYTHONIOENCODING = 'utf-8'
   $python = '.\.venv\Scripts\python.exe'
   & $python scripts\inspect_legal_rules.py `
       --rule-id BLDS_D117_K1_01 `
       --rules-dir data\rules `
       --output data\processed\training\BLDS_D117_K1_01.json
   if ($LASTEXITCODE -ne 0) { throw 'Xuất rule thất bại.' }

--all và --rule-id là hai chế độ loại trừ nhau. --rules-dir trỏ tới thư mục có
file rule JSON; chế độ --rule-id cần thêm thư mục catalogs bên trong. --output
chọn file JSON đầu ra; nếu bỏ qua, mỗi chế độ có file mặc định riêng.
Trên Windows, đặt PYTHONIOENCODING=utf-8 để hiển thị tiếng Việt trong terminal.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from src.common.setting_config import get_settings
from src.graph.graph_repository import LegalGraphRepository
from src.graph.graph_service import LegalGraphService
from src.graph.neo4j_client import Neo4jClient
from src.utils.file_util import FileUtil
from src.utils.logger import setup_logger

logger = setup_logger("inspect_legal_rules", "inspect_legal_rules.log")

BACKEND_DIR = FileUtil.get_project_root()
DEFAULT_RULES_DIR = BACKEND_DIR / "data" / "rules"
DEFAULT_OUTPUT_DIR = BACKEND_DIR / "data" / "processed"
DEFAULT_ALL_OUTPUT = DEFAULT_OUTPUT_DIR / "rule_graph_context_all.json"
DEFAULT_SINGLE_OUTPUT = DEFAULT_OUTPUT_DIR / "rule_graph_context_single.json"


def collect_predicates(rule: Mapping[str, Any]) -> list[str]:
    """Thu thập predicate theo thứ tự xuất hiện trong rule."""
    predicates: list[str] = []

    def visit(expression: Any) -> None:
        if (
            isinstance(expression, list)
            and len(expression) == 3
            and isinstance(expression[0], str)
            and isinstance(expression[1], str)
        ):
            if expression[0] not in predicates:
                predicates.append(expression[0])
            return
        if isinstance(expression, list):
            for child in expression:
                visit(child)
            return
        if isinstance(expression, dict):
            for child in expression.values():
                visit(child)

    visit(rule.get("when"))
    for exception in rule.get("unless", []):
        visit(exception)
    for effect in rule.get("then", []):
        predicate = effect.get("predicate")
        if isinstance(predicate, str) and predicate not in predicates:
            predicates.append(predicate)
    return predicates


def collect_node_references(rule: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Gom node ID nguồn và node ID được tham chiếu bởi rule links."""
    references_by_id: dict[str, list[dict[str, Any]]] = {}

    def add_reference(node_id: Any, reference: dict[str, Any]) -> None:
        if not isinstance(node_id, str) or not node_id:
            raise ValueError(f"Rule {rule.get('id')} chứa node_id không hợp lệ.")
        references_by_id.setdefault(node_id, []).append(reference)

    source = rule.get("source", {})
    source_node_ids = source.get("node_ids", []) if isinstance(source, Mapping) else []
    if not isinstance(source_node_ids, list):
        raise ValueError(f"source.node_ids của rule {rule.get('id')} phải là list.")
    for node_id in source_node_ids:
        add_reference(node_id, {"type": "source"})

    links = rule.get("links", [])
    if not isinstance(links, list):
        raise ValueError(f"links của rule {rule.get('id')} phải là list.")
    for link in links:
        if not isinstance(link, Mapping):
            raise ValueError(f"Rule {rule.get('id')} chứa link không hợp lệ.")
        reference = {"type": "link"}
        for field in ("rule_id", "relation", "note"):
            if field in link:
                reference[field] = link[field]
        add_reference(link.get("source_node_id"), reference)

    return [
        {"node_id": node_id, "references": references}
        for node_id, references in references_by_id.items()
    ]


class RuleInspector:
    """Đọc rule và lấy các node liên quan từ graph service."""

    def __init__(
        self,
        graph_repository: LegalGraphRepository,
        graph_service: LegalGraphService,
        rules_dir: Path = DEFAULT_RULES_DIR,
    ) -> None:
        """Khởi tạo inspector với graph repository/service và thư mục chứa rule."""
        self.graph_repository = graph_repository
        self.graph_service = graph_service
        self.rules_dir = Path(rules_dir)

    @staticmethod
    def _load_catalog(path: Path) -> dict[str, Any]:
        """Đọc catalog JSON từ đường dẫn cấu hình."""
        with path.open("r", encoding="utf-8") as file:
            catalog = json.load(file)
        if not isinstance(catalog, dict):
            raise ValueError(f"Catalog phải là object JSON: {path}")
        return catalog

    def load_rules(self) -> list[dict[str, Any]]:
        """Đọc toàn bộ rule từ các file JSON trực tiếp trong thư mục."""
        rule_files = sorted(self.rules_dir.glob("*.json"))
        if not rule_files:
            raise FileNotFoundError(f"Không tìm thấy rule JSON trong {self.rules_dir}.")

        rules: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for path in rule_files:
            with path.open("r", encoding="utf-8") as file:
                file_rules = json.load(file)
            if not isinstance(file_rules, list):
                raise ValueError(f"File rule phải chứa danh sách JSON: {path}")
            for rule in file_rules:
                if not isinstance(rule, dict) or not isinstance(rule.get("id"), str):
                    raise ValueError(f"Rule trong {path} thiếu id hợp lệ.")
                if rule["id"] in seen_ids:
                    raise ValueError(f"Rule ID bị trùng: {rule['id']}.")
                seen_ids.add(rule["id"])
                rules.append(rule)
        logger.info("Đã nạp %d rule từ %s.", len(rules), self.rules_dir)
        return rules

    def inspect_all(self) -> dict[str, Any]:
        """Xuất rule nguyên bản cùng dữ liệu graph cho toàn bộ rule."""
        rules = self.load_rules()
        nodes_by_id, citations_by_id = self._load_graph_context(rules)
        return {
            "mode": "all",
            "rules": [
                {
                    "rule": rule,
                    "related_nodes": self._format_related_nodes(
                        rule, nodes_by_id, citations_by_id
                    ),
                }
                for rule in rules
            ],
        }

    def inspect_one(self, rule_id: str) -> dict[str, Any]:
        """Xuất cấu trúc rule, catalogs và node graph liên quan."""
        if not rule_id.strip():
            raise ValueError("rule_id không được để trống.")
        matches = [rule for rule in self.load_rules() if rule["id"] == rule_id]
        if not matches:
            raise ValueError(f"Không tìm thấy rule có id '{rule_id}'.")

        rule = matches[0]
        nodes_by_id, citations_by_id = self._load_graph_context([rule])
        catalogs_dir = self.rules_dir / "catalogs"
        predicates_catalog = self._load_catalog(catalogs_dir / "predicates.json")[
            "predicates"
        ]
        effects_catalog = self._load_catalog(catalogs_dir / "effects.json")
        rule_kinds = effects_catalog["rule_kinds"]
        effects = effects_catalog["effects"]
        explanation_templates = self._load_catalog(catalogs_dir / "explanations.json")[
            "status_templates"
        ]
        predicate_names = collect_predicates(rule)
        unknown_predicates = [
            name for name in predicate_names if name not in predicates_catalog
        ]
        if unknown_predicates:
            raise ValueError(f"Predicate chưa có trong catalog: {unknown_predicates}.")

        kind = rule.get("kind")
        if kind not in rule_kinds:
            raise ValueError(f"Rule kind chưa có trong catalog: {kind}.")
        effect_names = list(
            dict.fromkeys(item["effect"] for item in rule.get("then", []))
        )
        unknown_effects = [name for name in effect_names if name not in effects]
        if unknown_effects:
            raise ValueError(f"Effect chưa có trong catalog: {unknown_effects}.")

        return {
            "mode": "single",
            "rule": rule,
            "rule_kind": {"name": kind, **rule_kinds[kind]},
            "predicates": {name: predicates_catalog[name] for name in predicate_names},
            "effects": {name: effects[name] for name in effect_names},
            "explanation_templates": explanation_templates,
            "related_nodes": self._format_related_nodes(
                rule, nodes_by_id, citations_by_id
            ),
        }

    def _load_graph_context(
        self, rules: list[dict[str, Any]]
    ) -> tuple[dict[str, dict[str, Any]], dict[str, str | None]]:
        """Tra cứu node ID duy nhất và citation path của từng node."""
        node_ids = list(
            dict.fromkeys(
                reference["node_id"]
                for rule in rules
                for reference in collect_node_references(rule)
            )
        )
        nodes = self.graph_repository.find_nodes_by_ids(node_ids)
        nodes_by_id = {node["node_id"]: node for node in nodes}
        missing_ids = sorted(set(node_ids) - set(nodes_by_id))
        if missing_ids:
            logger.warning("Không tìm thấy các node ID trong graph: %s", missing_ids)
        citations_by_id = {
            node_id: self.graph_service.get_citation_path(node_id)
            for node_id in nodes_by_id
        }
        return nodes_by_id, citations_by_id

    @staticmethod
    def _format_related_nodes(
        rule: Mapping[str, Any],
        nodes_by_id: Mapping[str, dict[str, Any]],
        citations_by_id: Mapping[str, str | None],
    ) -> list[dict[str, Any]]:
        """Tạo danh sách node cùng tham chiếu nguồn và citation cho một rule."""
        related_nodes = []
        for reference in collect_node_references(rule):
            node_id = reference["node_id"]
            node = nodes_by_id.get(node_id)
            related_nodes.append(
                {
                    **reference,
                    "found": node is not None,
                    "citation": citations_by_id.get(node_id),
                    "node": node,
                }
            )
        return related_nodes


def parse_args() -> argparse.Namespace:
    """Đọc tham số và hiển thị cách chạy script."""
    parser = argparse.ArgumentParser(
        description="Xuất rule pháp lý và node liên quan từ Neo4j ra JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--all",
        action="store_true",
        help="Đọc toàn bộ rule; mặc định ghi vào data\\processed\\rule_graph_context_all.json.",
    )
    mode.add_argument(
        "--rule-id",
        metavar="ID",
        help="Đọc một rule theo ID; mặc định ghi vào data\\processed\\rule_graph_context_single.json.",
    )
    parser.add_argument(
        "--rules-dir",
        type=Path,
        default=DEFAULT_RULES_DIR,
        help=f"Thư mục chứa rule JSON (mặc định: {DEFAULT_RULES_DIR}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Đường dẫn file JSON đầu ra; nếu bỏ qua sẽ dùng file mặc định theo chế độ.",
    )
    return parser.parse_args()


def serialize_graph_value(value: Any) -> str:
    """Chuyển kiểu ngày giờ của Neo4j sang chuỗi JSON ISO-8601."""
    if hasattr(value, "iso_format"):
        return value.iso_format()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"Không thể tuần tự hóa giá trị kiểu {type(value).__name__}.")


def main() -> int:
    """Chạy chế độ đọc rule đã chọn và ghi JSON ra file."""
    args = parse_args()
    output_path = args.output or (
        DEFAULT_ALL_OUTPUT if args.all else DEFAULT_SINGLE_OUTPUT
    )
    settings = get_settings()
    neo4j_client = Neo4jClient(
        uri=settings.neo4j_uri,
        username=settings.neo4j_username,
        password=settings.neo4j_password,
        database=settings.neo4j_database,
    )
    graph_repository = LegalGraphRepository(db=neo4j_client)
    graph_service = LegalGraphService(repository=graph_repository)
    try:
        inspector = RuleInspector(graph_repository, graph_service, args.rules_dir)
        result = (
            inspector.inspect_all() if args.all else inspector.inspect_one(args.rule_id)
        )
    finally:
        neo4j_client.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            result, file, ensure_ascii=False, indent=2, default=serialize_graph_value
        )
        file.write("\n")

    missing_node_ids = sorted(
        {
            node["node_id"]
            for entry in result["rules"]
            for node in entry["related_nodes"]
            if not node["found"]
        }
        if args.all
        else {node["node_id"] for node in result["related_nodes"] if not node["found"]}
    )
    logger.info("Đã ghi dữ liệu rule vào %s.", output_path)
    if missing_node_ids:
        logger.warning("Không tìm thấy các node ID: %s", missing_node_ids)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
