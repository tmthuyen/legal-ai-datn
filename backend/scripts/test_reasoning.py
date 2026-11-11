#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script CLI kiểm tra nhanh module reasoning (rule validation & reference evaluation) theo cấu trúc chuẩn.
Cách chạy từ thư mục backend:
    python scripts/test_reasoning.py
Hoặc từ root:
    python legal-ai-datn/backend/scripts/test_reasoning.py
"""

import json
import sys
from pathlib import Path

# Thêm thư mục backend vào sys.path để import src
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.reasoning.evaluator import evaluate_rule
from src.reasoning.validator import validate_rule

RULES_DIR = BACKEND_DIR / "data" / "rules"
PREDICATES_PATH = RULES_DIR / "catalogs" / "predicates.json"
EFFECTS_PATH = RULES_DIR / "catalogs" / "effects.json"
EXPLANATIONS_PATH = RULES_DIR / "catalogs" / "explanations.json"
NODES_PATH = BACKEND_DIR / "data" / "processed" / "nodes.json"
FIXTURES_PATH = BACKEND_DIR / "tests" / "fixtures" / "reasoning" / "rule_cases.jsonl"


def main() -> int:
    print("=" * 78)
    print("CHẠY KIỂM ĐỊNH & ĐÁNH GIÁ REASONING THEO CẤU TRÚC CODEBASE CHUẨN")
    print("=" * 78)

    # 1. Nạp dữ liệu
    with NODES_PATH.open("r", encoding="utf-8") as f:
        kg_node_ids = {str(n["node_id"]) for n in json.load(f) if "node_id" in n}

    with PREDICATES_PATH.open("r", encoding="utf-8") as f:
        predicates = json.load(f)["predicates"]

    with EFFECTS_PATH.open("r", encoding="utf-8") as f:
        effects = json.load(f)

    with EXPLANATIONS_PATH.open("r", encoding="utf-8") as f:
        explanations = json.load(f)["status_templates"]

    all_rules = []
    rules_by_id = {}
    for rf in sorted(RULES_DIR.glob("*.json")):
        with rf.open("r", encoding="utf-8") as f:
            for r in json.load(f):
                rules_by_id[r["id"]] = r
                all_rules.append(r)

    # 2. Kiểm định Rule Schema & KG
    val_errors = []
    all_rule_ids = set(rules_by_id.keys())
    for r in all_rules:
        errs = validate_rule(r, predicates, effects, kg_node_ids, all_rule_ids)
        val_errors.extend(errs)

    if val_errors:
        print("[FAIL] Phát hiện lỗi trong các quy tắc:")
        for e in val_errors:
            print(f"  - {e}")
        return 1

    print(f"[PASS] 100% {len(all_rules)} quy tắc đã vượt qua kiểm định tính hợp lệ.")

    # 3. Đánh giá toàn bộ test cases trong fixture reasoning
    passed = 0
    total = 0
    with FIXTURES_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            case = json.loads(line)
            cid = case["case_id"]
            rid = case["rule_id"]
            expected = case["expected"]

            rule = rules_by_id[rid]
            actual = evaluate_rule(rule, case["facts"], explanations)

            app_ok = actual["applicability_status"] == expected["applicability_status"]
            comp_ok = actual["compliance_status"] == expected["compliance_status"]
            miss_ok = actual["missing_facts"] == expected["missing_facts"]
            deriv_ok = True
            if "derived_facts" in expected:
                deriv_ok = actual["derived_facts"] == expected["derived_facts"]

            if app_ok and comp_ok and miss_ok and deriv_ok:
                passed += 1
            else:
                print(f"[FAIL] {cid}\n  Expected: {expected}\n  Actual: {actual}")

    print(f"[PASS] Đánh giá suy luận: {passed}/{total} test cases PASS ({passed/total*100:.1f}%)")
    print("=" * 78)
    return 0 if (passed == total) else 1


if __name__ == "__main__":
    sys.exit(main())

