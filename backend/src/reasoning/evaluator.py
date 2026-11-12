# -*- coding: utf-8 -*-
"""
Bộ đánh giá quy tắc (Rule Evaluator) theo logic 3 giá trị Kleene K3.
Phân biệt tách biệt Applicability và Compliance.
Module: backend.src.reasoning.evaluator
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TRUE = "TRUE"
FALSE = "FALSE"
UNKNOWN = "UNKNOWN"

_DEFAULT_EXPLANATIONS_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "rules"
    / "catalogs"
    / "explanations.json"
)


def _load_default_explanations() -> Dict[str, str]:
    with _DEFAULT_EXPLANATIONS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)["status_templates"]


def _dedup_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def eval_atomic(
    predicate: str, operator: str, target_val: Any, facts: Dict[str, Any]
) -> Tuple[str, List[str]]:
    if operator == "exists":
        present = predicate in facts and facts[predicate] is not None
        return (TRUE if (present == target_val) else FALSE), []

    if predicate not in facts or facts[predicate] is None:
        return UNKNOWN, [predicate]

    actual_val = facts[predicate]

    if operator == "eq":
        res = actual_val == target_val and type(actual_val) is type(target_val)
    elif operator == "neq":
        res = actual_val != target_val or type(actual_val) is not type(target_val)
    elif operator == "gt":
        res = actual_val > target_val
    elif operator == "gte":
        res = actual_val >= target_val
    elif operator == "lt":
        res = actual_val < target_val
    elif operator == "lte":
        res = actual_val <= target_val
    elif operator == "in":
        res = actual_val in target_val
    elif operator == "not_in":
        res = actual_val not in target_val
    else:
        raise ValueError(f"Toán tử không được hỗ trợ: {operator}")

    return (TRUE if res else FALSE), []


def eval_condition_k3(expr: Any, facts: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Đánh giá biểu thức điều kiện theo logic 3 giá trị Kleene K3:
    - all (AND): FALSE nếu có ít nhất 1 nhánh FALSE; TRUE nếu mọi nhánh TRUE; ngược lại UNKNOWN.
    - any (OR) : TRUE nếu có ít nhất 1 nhánh TRUE; FALSE nếu mọi nhánh FALSE; ngược lại UNKNOWN.
    - not (NOT): TRUE <-> FALSE; UNKNOWN -> UNKNOWN.
    """
    if isinstance(expr, list):
        pred, op, val = expr
        return eval_atomic(pred, op, val, facts)

    if isinstance(expr, dict):
        if "not" in expr:
            child_val, child_missing = eval_condition_k3(expr["not"], facts)
            if child_val == TRUE:
                return FALSE, []
            if child_val == FALSE:
                return TRUE, []
            return UNKNOWN, child_missing

        if "all" in expr:
            missing_acc: List[str] = []
            has_unknown = False
            for child in expr["all"]:
                c_val, c_missing = eval_condition_k3(child, facts)
                if c_val == FALSE:
                    return FALSE, []
                if c_val == UNKNOWN:
                    has_unknown = True
                    missing_acc.extend(c_missing)
            if has_unknown:
                return UNKNOWN, _dedup_preserve_order(missing_acc)
            return TRUE, []

        if "any" in expr:
            missing_acc = []
            has_unknown = False
            for child in expr["any"]:
                c_val, c_missing = eval_condition_k3(child, facts)
                if c_val == TRUE:
                    return TRUE, []
                if c_val == UNKNOWN:
                    has_unknown = True
                    missing_acc.extend(c_missing)
            if has_unknown:
                return UNKNOWN, _dedup_preserve_order(missing_acc)
            return FALSE, []

    raise ValueError(f"Biểu thức điều kiện không hợp lệ: {expr!r}")


def evaluate_rule(
    rule: Dict[str, Any],
    facts: Dict[str, Any],
    explanations_templates: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    rule_id = rule["id"]
    if explanations_templates is None:
        explanations_templates = _load_default_explanations()

    # Bước 1: Đánh giá điều kiện kích hoạt (when)
    when_val, when_missing = eval_condition_k3(rule["when"], facts)

    if when_val == FALSE:
        return {
            "rule_id": rule_id,
            "applicability_status": "NOT_APPLICABLE",
            "compliance_status": "NOT_EVALUATED",
            "missing_facts": [],
            "derived_facts": {},
            "explanation": explanations_templates["NOT_APPLICABLE"].format(
                rule_id=rule_id
            ),
        }

    if when_val == UNKNOWN:
        return {
            "rule_id": rule_id,
            "applicability_status": "INDETERMINATE",
            "compliance_status": "NOT_EVALUATED",
            "missing_facts": when_missing,
            "derived_facts": {},
            "explanation": explanations_templates["INDETERMINATE"].format(
                rule_id=rule_id, missing_facts=", ".join(when_missing)
            ),
        }

    # Bước 2: when == TRUE -> Đánh giá ngoại lệ (unless)
    unless_list = rule.get("unless", [])
    if unless_list:
        unless_missing: List[str] = []
        has_unknown_unless = False
        for u_expr in unless_list:
            u_val, u_miss = eval_condition_k3(u_expr, facts)
            if u_val == TRUE:
                return {
                    "rule_id": rule_id,
                    "applicability_status": "EXCEPTED",
                    "compliance_status": "NOT_EVALUATED",
                    "missing_facts": [],
                    "derived_facts": {},
                    "explanation": explanations_templates["EXCEPTED"].format(
                        rule_id=rule_id
                    ),
                }
            if u_val == UNKNOWN:
                has_unknown_unless = True
                unless_missing.extend(u_miss)

        if has_unknown_unless:
            dedup_u_missing = _dedup_preserve_order(unless_missing)
            return {
                "rule_id": rule_id,
                "applicability_status": "EXCEPTION_INDETERMINATE",
                "compliance_status": "NOT_EVALUATED",
                "missing_facts": dedup_u_missing,
                "derived_facts": {},
                "explanation": explanations_templates["EXCEPTION_INDETERMINATE"].format(
                    rule_id=rule_id, missing_facts=", ".join(dedup_u_missing)
                ),
            }

    # Bước 3: when == TRUE và mọi unless == FALSE (hoặc rỗng) -> Rule APPLICABLE
    # Tiến hành đánh giá phần then (Compliance / Derivation)
    then_missing: List[str] = []
    derived_facts: Dict[str, Any] = {}
    has_violation = False
    has_indeterminate = False
    has_derivation = False

    for item in rule["then"]:
        eff = item["effect"]
        pred = item["predicate"]
        op = item.get("operator", "eq")
        val = item["value"]

        if eff == "REQUIRE":
            t_val, t_miss = eval_atomic(pred, op, val, facts)
            if t_val == FALSE:
                has_violation = True
            elif t_val == UNKNOWN:
                has_indeterminate = True
                then_missing.extend(t_miss)
        elif eff == "PROHIBIT":
            t_val, t_miss = eval_atomic(pred, op, val, facts)
            if t_val == TRUE:
                has_violation = True
            elif t_val == UNKNOWN:
                has_indeterminate = True
                then_missing.extend(t_miss)
        elif eff in ("DERIVE", "DENY_RECOGNITION", "PERMIT"):
            has_derivation = True
            derived_facts[pred] = val
        else:
            raise ValueError(f"Effect không được hỗ trợ: {eff}")

    if has_violation:
        comp_status = "VIOLATED"
        final_missing: List[str] = []
        expl = explanations_templates["APPLICABLE_VIOLATED"].format(rule_id=rule_id)
    elif has_indeterminate:
        comp_status = "INDETERMINATE"
        final_missing = _dedup_preserve_order(then_missing)
        expl = explanations_templates["APPLICABLE_INDETERMINATE"].format(
            rule_id=rule_id, missing_facts=", ".join(final_missing)
        )
    elif has_derivation:
        comp_status = "DERIVED"
        final_missing = []
        expl = explanations_templates["APPLICABLE_DERIVED"].format(
            rule_id=rule_id, derived_facts=json.dumps(derived_facts, ensure_ascii=False)
        )
    else:
        comp_status = "COMPLIANT"
        final_missing = []
        expl = explanations_templates["APPLICABLE_COMPLIANT"].format(rule_id=rule_id)

    return {
        "rule_id": rule_id,
        "applicability_status": "APPLICABLE",
        "compliance_status": comp_status,
        "missing_facts": final_missing,
        "derived_facts": derived_facts,
        "explanation": expl,
    }
