# -*- coding: utf-8 -*-
"""
Unit tests cho logic kiểm định Rule (Schema, Predicate Catalog, KG existence, Link integrity, Negative tests).
"""

import copy
import json
from pathlib import Path

from src.reasoning.validator import validate_rule

BASE_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
RULES_DIR = BASE_BACKEND_DIR / "data" / "rules"
PREDICATES_PATH = RULES_DIR / "catalogs" / "predicates.json"
EFFECTS_PATH = RULES_DIR / "catalogs" / "effects.json"
NODES_PATH = BASE_BACKEND_DIR / "data" / "processed" / "nodes.json"


def load_context():
    with NODES_PATH.open("r", encoding="utf-8") as f:
        kg_node_ids = {str(n["node_id"]) for n in json.load(f) if "node_id" in n}

    with PREDICATES_PATH.open("r", encoding="utf-8") as f:
        predicates_catalog = json.load(f)["predicates"]

    with EFFECTS_PATH.open("r", encoding="utf-8") as f:
        effects_catalog = json.load(f)

    all_rules = []
    all_rule_ids = set()
    for rf in sorted(RULES_DIR.glob("*.json")):
        with rf.open("r", encoding="utf-8") as f:
            for r in json.load(f):
                all_rule_ids.add(r["id"])
                all_rules.append(r)

    return kg_node_ids, predicates_catalog, effects_catalog, all_rules, all_rule_ids


def test_all_deployed_rules_are_valid():
    """Tất cả 15 quy tắc mẫu đã triển khai phải vượt qua 100% kiểm định."""
    kg_nodes, predicates, effects, all_rules, all_rule_ids = load_context()
    for rule in all_rules:
        errors = validate_rule(rule, predicates, effects, kg_nodes, all_rule_ids)
        assert errors == [], f"Quy tắc {rule.get('id')} có lỗi: {errors}"


def test_negative_scenarios_are_caught():
    """Kiểm tra validator bắt đúng 6 loại lỗi âm tính."""
    kg_nodes, predicates, effects, all_rules, all_rule_ids = load_context()
    sample = copy.deepcopy(all_rules[0])

    # 1. Thiếu trường bắt buộc
    r1 = copy.deepcopy(sample)
    del r1["unless"]
    err1 = validate_rule(r1, predicates, effects, kg_nodes, all_rule_ids)
    assert any("Thiếu trường bắt buộc" in e for e in err1)

    # 2. Vị từ không khai báo trong catalog
    r2 = copy.deepcopy(sample)
    r2["when"] = {"all": [["unknown.predicate", "eq", True]]}
    err2 = validate_rule(r2, predicates, effects, kg_nodes, all_rule_ids)
    assert any("chưa được khai báo" in e for e in err2)

    # 3. Giá trị enum không hợp lệ
    r3 = copy.deepcopy(sample)
    r3["when"] = {"all": [["asset.ownership", "eq", "INVALID_VAL"]]}
    err3 = validate_rule(r3, predicates, effects, kg_nodes, all_rule_ids)
    assert any("không thuộc tập enum" in e for e in err3)

    # 4. Toán tử không hợp lệ
    r4 = copy.deepcopy(sample)
    r4["when"] = {"all": [["asset.ownership", "approx", "JOINT_SPOUSAL"]]}
    err4 = validate_rule(r4, predicates, effects, kg_nodes, all_rule_ids)
    assert any("không hợp lệ" in e for e in err4)

    # 5. Node KG không tồn tại
    r5 = copy.deepcopy(sample)
    r5["source"]["node_ids"] = ["LUAT_HNGD_2014_D999"]
    err5 = validate_rule(r5, predicates, effects, kg_nodes, all_rule_ids)
    assert any("KHÔNG tồn tại trong nodes.json" in e for e in err5)

    # 6. Rule link gãy
    r6 = copy.deepcopy(sample)
    r6["links"] = [
        {
            "rule_id": "FAKE_RULE_999",
            "relation": "RELATED_PROVISION",
            "source_node_id": "LUAT_HNGD_2014_D24_K2",
        }
    ]
    err6 = validate_rule(r6, predicates, effects, kg_nodes, all_rule_ids)
    assert any("không tồn tại trong tập rule" in e for e in err6)
