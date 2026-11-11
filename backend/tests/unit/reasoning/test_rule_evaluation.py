# -*- coding: utf-8 -*-
"""
Unit tests cho logic đánh giá Rule (Kleene K3 3-valued logic, Applicability & Compliance separation).
Chạy trên 30 tình huống kiểm thử trong backend/tests/fixtures/reasoning/rule_cases.jsonl.
"""

import json
from pathlib import Path

from src.reasoning.evaluator import evaluate_rule

BASE_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
RULES_DIR = BASE_BACKEND_DIR / "data" / "rules"
EXPLANATIONS_PATH = RULES_DIR / "catalogs" / "explanations.json"
FIXTURES_PATH = (
    BASE_BACKEND_DIR / "tests" / "fixtures" / "reasoning" / "rule_cases.jsonl"
)


def test_reference_rule_cases_all_pass():
    """Kiểm tra 30 test cases chuẩn đạt 100% kết quả mong đợi."""
    rules_by_id = {}
    for rf in sorted(RULES_DIR.glob("*.json")):
        with rf.open("r", encoding="utf-8") as f:
            for r in json.load(f):
                rules_by_id[r["id"]] = r

    with EXPLANATIONS_PATH.open("r", encoding="utf-8") as f:
        explanations_templates = json.load(f)["status_templates"]

    with FIXTURES_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            case = json.loads(line)
            cid = case["case_id"]
            rid = case["rule_id"]
            expected = case["expected"]

            assert rid in rules_by_id, f"Rule {rid} không tồn tại cho case {cid}"
            rule = rules_by_id[rid]
            actual = evaluate_rule(rule, case["facts"], explanations_templates)

            assert (
                actual["applicability_status"] == expected["applicability_status"]
            ), f"[{cid}] Applicability status không khớp. Expected: {expected['applicability_status']}, Actual: {actual['applicability_status']}"
            assert (
                actual["compliance_status"] == expected["compliance_status"]
            ), f"[{cid}] Compliance status không khớp. Expected: {expected['compliance_status']}, Actual: {actual['compliance_status']}"
            assert (
                actual["missing_facts"] == expected["missing_facts"]
            ), f"[{cid}] missing_facts không khớp. Expected: {expected['missing_facts']}, Actual: {actual['missing_facts']}"
            if "derived_facts" in expected:
                assert (
                    actual["derived_facts"] == expected["derived_facts"]
                ), f"[{cid}] derived_facts không khớp. Expected: {expected['derived_facts']}, Actual: {actual['derived_facts']}"
