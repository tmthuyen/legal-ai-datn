import re
import unicodedata

from src.utils.teencode_dict import (
    COMMON_ABBREVIATIONS,
    EMOJI_MAP,
    TEENCODE_MAP,
    normalize_typing_rules,
)


class CleanTextUtil:
    # map emoji
    @staticmethod
    def map_emoji(text: str) -> str:
        for icon, token in EMOJI_MAP.items():
            text = text.replace(icon, f" {token} ")
        return text

    # map teencode and common abbreviations
    @staticmethod
    def map_rule(text: str) -> str:
        # lower
        text = text.lower()

        # Teencode hoặc từ viết tắt → tiếng Việt chuẩn
        words = text.split()
        clean_words = []
        for w in words:
            w = TEENCODE_MAP.get(w, w)  # Thay thế teencode
            w = COMMON_ABBREVIATIONS.get(w, w)  # Thay thế từ viết tắt phổ biến
            w = normalize_typing_rules(w)
            w = w.strip()  # Xóa khoảng trắng đầu và cuối
            clean_words.append(w)
        return " ".join(clean_words)

    # normalize NFC
    @staticmethod
    def normalize_nfc(text: str) -> str:
        return unicodedata.normalize("NFC", text)

    # clean trash characters
    @staticmethod
    def clean_trash_characters(text: str) -> str:
        # Loại bỏ các ký tự không mong muốn còn sót
        # Ký tự rác ==> space
        text = re.sub(
            r"[^\w\s<>"
            r"àáâãèéêìíòóôõùúýăđơư"
            r"ạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ"
            r"]",
            " ",
            text,
        )
        text = re.sub(r"\s+", " ", text)  # Xóa khoảng trắng thừa
        text = text.strip()  # Xóa khoảng trắng đầu và cuối
        return text
