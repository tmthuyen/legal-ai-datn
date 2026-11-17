# test clean text util

from src.utils.clean_text_utils import CleanTextUtil


# test normalize_nfc
def test_normalize_nfc():
    text = "café"
    normalized_text = CleanTextUtil.normalize_nfc(text)
    assert normalized_text == "café"


# test clean_trash_characters
def test_clean_trash_characters():
    text = "Hello, World! @#$%^&*()"
    cleaned_text = CleanTextUtil.clean_trash_characters(text)
    assert cleaned_text == "Hello World"
