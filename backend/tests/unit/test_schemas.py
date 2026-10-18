# backend/tests/unit/test_schemas.py
import pytest
from src.common.schemas import LegalHierarchy
from src.common.custom_exception import CustomException

def test_hierarchy_valid_article_clause():
    """Khoản và Điều hợp lệ."""
    h = LegalHierarchy(document="BLDS_2015", article="27", clause="1")
    valid, err = h.validate(require_document=False)
    assert valid is True

def test_hierarchy_invalid_point_without_clause():
    """Điểm không thể đứng một mình mà không có Khoản."""
    h = LegalHierarchy(document="BLDS_2015", point="a")
    valid, err = h.validate(require_document=False)
    assert valid is False
