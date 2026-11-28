import pytest

from src.reasoning.fact_extractor import FactExtractionError, FactExtractor

PREDICATES = {
    "child.age": {"type": "integer", "domain": "tort"},
    "tort.caused_by_child": {"type": "boolean", "domain": "tort"},
    "child.property_sufficient_for_compensation": {
        "type": "boolean",
        "domain": "tort",
    },
    "child.must_compensate_with_own_property": {
        "type": "boolean",
        "domain": "tort",
    },
    "asset.ownership": {
        "type": "enum",
        "allowed_values": ["JOINT_SPOUSAL", "SEPARATE"],
        "domain": "asset",
    },
}

RULE = {
    "id": "BLDS_D586_K2_04",
    "when": {
        "all": [
            ["tort.caused_by_child", "eq", True],
            ["child.age", "gte", 15],
            ["child.age", "lt", 18],
            ["child.property_sufficient_for_compensation", "eq", False],
        ]
    },
    "unless": [],
    "then": [
        {
            "effect": "DERIVE",
            "predicate": "parent.must_compensate_deficiency",
            "value": True,
        }
    ],
}


class FakeModel:
    def __init__(self, output):
        self.output = output
        self.calls = []

    def predict(self, task_id, input_text):
        self.calls.append((task_id, input_text))
        return {"result": {"output": self.output}}


def test_collect_rule_predicates_excludes_derived_output():
    extractor = FactExtractor(predicates_catalog=PREDICATES)

    assert extractor.collect_rule_predicates(RULE) == [
        "tort.caused_by_child",
        "child.age",
        "child.property_sufficient_for_compensation",
    ]


def test_build_prompt_contains_only_rule_predicates():
    extractor = FactExtractor(predicates_catalog=PREDICATES)

    prompt = extractor.build_prompt("Người 16 tuổi gây thiệt hại.", RULE)

    assert "child.age" in prompt
    assert "parent.must_compensate_deficiency" not in prompt
    assert "Không tự suy diễn kết luận pháp lý" in prompt


def test_extract_validates_model_output_and_reports_missing_facts():
    model = FakeModel(
        {
            "facts": {"tort.caused_by_child": True, "child.age": 16},
            "missing_facts": [],
            "evidence": {"child.age": "16 tuổi"},
        }
    )
    extractor = FactExtractor(model=model, predicates_catalog=PREDICATES)

    result = extractor.extract("Người 16 tuổi gây thiệt hại.", RULE)

    assert result["facts"] == {"tort.caused_by_child": True, "child.age": 16}
    assert result["missing_facts"] == ["child.property_sufficient_for_compensation"]
    assert model.calls[0][0] == "LEGAL_FACT_EXTRACTION"


def test_validate_output_rejects_invalid_enum_and_unknown_predicate():
    extractor = FactExtractor(predicates_catalog=PREDICATES)
    rule = {
        "id": "asset-rule",
        "when": [["asset.ownership", "eq", "JOINT_SPOUSAL"]],
        "unless": [],
        "then": [],
    }

    with pytest.raises(FactExtractionError, match="Predicate không thuộc rule"):
        extractor.validate_output(
            {
                "facts": {
                    "asset.ownership": "UNKNOWN_VALUE",
                    "child.age": 16,
                },
                "missing_facts": [],
                "evidence": {},
            },
            rule,
        )


def test_unwrap_model_output_handles_markdown_code_fences():
    extractor = FactExtractor(predicates_catalog=PREDICATES)
    raw_markdown = """```json
{
    "facts": {"tort.caused_by_child": true, "child.age": 16},
    "missing_facts": [],
    "evidence": {"child.age": "16 tuổi"}
}
```"""
    parsed = extractor._unwrap_model_output({"result": {"output": raw_markdown}})
    assert parsed["facts"]["child.age"] == 16
    assert parsed["facts"]["tort.caused_by_child"] is True
