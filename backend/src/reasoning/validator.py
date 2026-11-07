# -*- coding: utf-8 -*-
"""
Trình kiểm định cấu trúc, danh mục vị từ và liên kết Đồ thị Tri thức cho Legal Rule Specification V1.
Module: backend.src.reasoning.validator
"""

import copy
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

ALLOWED_OPERATORS = {"eq", "neq", "gt", "gte", "lt", "lte", "in", "not_in", "exists"}
ALLOWED_DOC_VERSIONS = {"ORIGINAL", "AMENDED", "CONSOLIDATED"}
ALLOWED_STATUSES = {"DRAFT", "PENDING_REVIEW", "VERIFIED", "DEPRECATED"}
ALLOWED_LINK_RELATIONS = {
    "RELATED_PROVISION",
    "REQUIRES_STATUTORY_GROUND",
    "EXCEPTION_REFERENCE",
    "PREREQUISITE_CONDITION",
    "CONSEQUENCE_OF_VIOLATION",
}
REQUIRED_RULE_FIELDS = {
    "schema_version",
    "id",
    "source",
    "kind",
    "when",
    "then",
    "unless",
    "links",
    "meta",
    "extensions",
}
RULE_ID_PATTERN = re.compile(r"^[A-Z0-9_]+$")


def check_value_against_predicate(
    pred_name: str,
    operator: str,
    value: Any,
    predicates_catalog: Dict[str, Any],
    context: str,
) -> List[str]:
    errors: List[str] = []
    if pred_name not in predicates_catalog:
        errors.append(
            f"[{context}] Vị từ '{pred_name}' chưa được khai báo trong catalogs/predicates.json."
        )
        return errors

    if operator not in ALLOWED_OPERATORS:
        errors.append(
            f"[{context}] Toán tử '{operator}' không hợp lệ (chỉ cho phép {sorted(ALLOWED_OPERATORS)})."
        )
        return errors

    spec = predicates_catalog[pred_name]
    expected_type = spec["type"]

    if operator == "exists":
        if not isinstance(value, bool):
            errors.append(
                f"[{context}] Toán tử 'exists' yêu cầu value kiểu boolean cho '{pred_name}'."
            )
        return errors

    values_to_check = value if operator in ("in", "not_in") else [value]
    if operator in ("in", "not_in") and not isinstance(value, list):
        errors.append(
            f"[{context}] Toán tử '{operator}' yêu cầu value là một danh sách (list)."
        )
        return errors

    for v in values_to_check:
        if expected_type == "boolean":
            if not isinstance(v, bool):
                errors.append(
                    f"[{context}] Vị từ '{pred_name}' yêu cầu kiểu boolean, nhận được {type(v).__name__} ({v!r})."
                )
            if operator in ("gt", "gte", "lt", "lte"):
                errors.append(
                    f"[{context}] Không dùng toán tử so sánh đại số '{operator}' cho vị từ boolean '{pred_name}'."
                )
        elif expected_type == "integer":
            if not isinstance(v, int) or isinstance(v, bool):
                errors.append(
                    f"[{context}] Vị từ '{pred_name}' yêu cầu kiểu integer, nhận được {v!r}."
                )
        elif expected_type == "number":
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                errors.append(
                    f"[{context}] Vị từ '{pred_name}' yêu cầu kiểu number, nhận được {v!r}."
                )
        elif expected_type == "enum":
            allowed = spec.get("allowed_values", [])
            if not isinstance(v, str) or v not in allowed:
                errors.append(
                    f"[{context}] Giá trị '{v}' của vị từ '{pred_name}' không thuộc tập enum cho phép {allowed}."
                )
            if operator in ("gt", "gte", "lt", "lte"):
                errors.append(
                    f"[{context}] Không dùng toán tử '{operator}' cho vị từ enum '{pred_name}'."
                )
        elif expected_type == "string":
            if not isinstance(v, str):
                errors.append(
                    f"[{context}] Vị từ '{pred_name}' yêu cầu kiểu string, nhận được {v!r}."
                )

    return errors


def validate_condition_expr(
    expr: Any,
    predicates_catalog: Dict[str, Any],
    context: str,
) -> List[str]:
    errors: List[str] = []
    if isinstance(expr, list):
        if len(expr) != 3:
            errors.append(
                f"[{context}] Điều kiện nguyên tử phải là mảng 3 phần tử [predicate, operator, value], nhận được {expr!r}."
            )
            return errors
        pred, op, val = expr
        if not isinstance(pred, str) or not isinstance(op, str):
            errors.append(
                f"[{context}] Predicate và operator phải là chuỗi trong {expr!r}."
            )
            return errors
        errors.extend(
            check_value_against_predicate(pred, op, val, predicates_catalog, context)
        )
    elif isinstance(expr, dict):
        if set(expr.keys()) not in ({"all"}, {"any"}, {"not"}):
            errors.append(
                f"[{context}] Biểu thức logic chỉ được chứa duy nhất một khóa trong ('all', 'any', 'not'), nhận được {list(expr.keys())}."
            )
            return errors
        if "not" in expr:
            errors.extend(
                validate_condition_expr(
                    expr["not"], predicates_catalog, f"{context}.not"
                )
            )
        else:
            key = "all" if "all" in expr else "any"
            children = expr[key]
            if not isinstance(children, list) or len(children) == 0:
                errors.append(
                    f"[{context}.{key}] Danh sách con của '{key}' phải là mảng không rỗng."
                )
                return errors
            for idx, child in enumerate(children):
                errors.extend(
                    validate_condition_expr(
                        child, predicates_catalog, f"{context}.{key}[{idx}]"
                    )
                )
    else:
        errors.append(f"[{context}] Biểu thức điều kiện không hợp lệ: {expr!r}.")
    return errors


def validate_rule(
    rule: Dict[str, Any],
    predicates_catalog: Dict[str, Any],
    effects_catalog: Dict[str, Any],
    kg_node_ids: Set[str],
    all_rule_ids: Set[str],
) -> List[str]:
    errors: List[str] = []
    rule_id = str(rule.get("id", "<UNKNOWN_ID>"))
    ctx = f"Rule:{rule_id}"

    actual_fields = set(rule.keys())
    missing = REQUIRED_RULE_FIELDS - actual_fields
    extra = actual_fields - REQUIRED_RULE_FIELDS
    if missing:
        errors.append(f"[{ctx}] Thiếu trường bắt buộc: {sorted(missing)}.")
    if extra:
        errors.append(
            f"[{ctx}] Chứa trường không được phép ở cấp cao nhất: {sorted(extra)}."
        )
    if missing:
        return errors

    if rule["schema_version"] != "1.0":
        errors.append(
            f"[{ctx}] schema_version phải là '1.0', nhận được {rule['schema_version']!r}."
        )

    if not isinstance(rule["id"], str) or not RULE_ID_PATTERN.match(rule["id"]):
        errors.append(f"[{ctx}] id '{rule['id']}' không khớp mẫu ^[A-Z0-9_]+$.")

    source = rule["source"]
    if not isinstance(source, dict) or set(source.keys()) != {
        "node_ids",
        "document_version",
    }:
        errors.append(
            f"[{ctx}] source phải chứa đúng 'node_ids' và 'document_version'."
        )
    else:
        node_ids = source["node_ids"]
        if not isinstance(node_ids, list) or len(node_ids) == 0:
            errors.append(f"[{ctx}] source.node_ids phải là danh sách không rỗng.")
        else:
            for nid in node_ids:
                if nid not in kg_node_ids:
                    errors.append(
                        f"[{ctx}] source.node_ids chứa node_id '{nid}' KHÔNG tồn tại trong nodes.json."
                    )
        if source["document_version"] not in ALLOWED_DOC_VERSIONS:
            errors.append(
                f"[{ctx}] source.document_version '{source['document_version']}' không hợp lệ."
            )

    if rule["kind"] not in effects_catalog.get("rule_kinds", {}):
        errors.append(
            f"[{ctx}] kind '{rule['kind']}' không tồn tại trong catalogs/effects.json."
        )

    errors.extend(
        validate_condition_expr(rule["when"], predicates_catalog, f"{ctx}.when")
    )

    if not isinstance(rule["unless"], list):
        errors.append(f"[{ctx}] unless phải là một danh sách.")
    else:
        for idx, u_expr in enumerate(rule["unless"]):
            errors.extend(
                validate_condition_expr(
                    u_expr, predicates_catalog, f"{ctx}.unless[{idx}]"
                )
            )

    then_list = rule["then"]
    if not isinstance(then_list, list) or len(then_list) == 0:
        errors.append(f"[{ctx}] then phải là danh sách không rỗng.")
    else:
        for idx, item in enumerate(then_list):
            t_ctx = f"{ctx}.then[{idx}]"
            if not isinstance(item, dict) or not {
                "effect",
                "predicate",
                "value",
            }.issubset(item.keys()):
                errors.append(
                    f"[{t_ctx}] Mỗi phần tử then phải chứa 'effect', 'predicate', 'value'."
                )
                continue
            eff = item["effect"]
            pred = item["predicate"]
            op = item.get("operator", "eq")
            val = item["value"]
            if eff not in effects_catalog.get("effects", {}):
                errors.append(
                    f"[{t_ctx}] effect '{eff}' không tồn tại trong catalogs/effects.json."
                )
            errors.extend(
                check_value_against_predicate(pred, op, val, predicates_catalog, t_ctx)
            )

    if not isinstance(rule["links"], list):
        errors.append(f"[{ctx}] links phải là một danh sách.")
    else:
        for idx, link in enumerate(rule["links"]):
            l_ctx = f"{ctx}.links[{idx}]"
            if not isinstance(link, dict) or not {
                "rule_id",
                "relation",
                "source_node_id",
            }.issubset(link.keys()):
                errors.append(
                    f"[{l_ctx}] link phải chứa 'rule_id', 'relation', 'source_node_id'."
                )
                continue
            if link["rule_id"] not in all_rule_ids:
                errors.append(
                    f"[{l_ctx}] rule_id đích '{link['rule_id']}' không tồn tại trong tập rule hiện hành."
                )
            if link["relation"] not in ALLOWED_LINK_RELATIONS:
                errors.append(f"[{l_ctx}] relation '{link['relation']}' không hợp lệ.")
            if link["source_node_id"] not in kg_node_ids:
                errors.append(
                    f"[{l_ctx}] source_node_id '{link['source_node_id']}' không tồn tại trong nodes.json."
                )

    meta = rule["meta"]
    if not isinstance(meta, dict) or set(meta.keys()) != {
        "status",
        "revision",
        "description",
    }:
        errors.append(
            f"[{ctx}] meta phải chứa đúng 'status', 'revision', 'description'."
        )
    else:
        if meta["status"] not in ALLOWED_STATUSES:
            errors.append(f"[{ctx}] meta.status '{meta['status']}' không hợp lệ.")
        if not isinstance(meta["revision"], int) or meta["revision"] < 1:
            errors.append(f"[{ctx}] meta.revision phải là số nguyên >= 1.")
        if (
            not isinstance(meta["description"], str)
            or len(meta["description"].strip()) < 5
        ):
            errors.append(f"[{ctx}] meta.description phải là chuỗi mô tả có ý nghĩa.")

    if not isinstance(rule["extensions"], dict):
        errors.append(f"[{ctx}] extensions phải là một object (dict).")

    return errors
