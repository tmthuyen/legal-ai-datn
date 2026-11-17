# test file util


from unittest.mock import patch

import pytest

from src.utils.file_util import FileUtil


def test_get_project_root_success():
    project_root = FileUtil.get_project_root()
    assert project_root.name == "backend"


def test_get_project_root_failure():
    wrong_path = "/user/wrong/src/utils/file_util.py"

    with patch("src.utils.file_util.__file__", new=wrong_path):
        with pytest.raises(Exception) as exc_info:
            FileUtil.get_project_root()
    assert "Expected project root to be 'backend'" in str(exc_info.value)


def test_get_data_dir():
    data_dir = FileUtil.get_data_dir()
    assert data_dir.name == "data"
    assert data_dir.exists()


def test_get_models_dir():
    models_dir = FileUtil.get_models_dir()
    assert models_dir.name == "models"
    assert models_dir.exists()
