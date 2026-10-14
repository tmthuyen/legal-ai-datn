"""
constants.py
Module quản lý các hằng số cho Legal Knowledge Graph.

Nhiệm vụ:
- Định nghĩa các hằng số dùng chung trong hệ thống
- Bất kỳ hằng số nào được sử dụng trong nhiều module nên được định nghĩa ở đây để tránh trùng lặp và dễ bảo trì.
- Cung cấp một điểm tập trung cho các giá trị hằng số, giúp dễ dàng quản lý và cập nhật.
"""

# Dùng cho phần
# Ánh xạ số La Mã, số nguyên sang từ thứ tự tiếng Việt
FROM_NUMBER_TO_VIETNAMESE_ORDINALS = {
    1: "nhất",
    2: "hai",
    3: "ba",
    4: "bốn",
    5: "năm",
    6: "sáu",
    7: "bảy",
    8: "tám",
    9: "chín",
    10: "mười",
    11: "mười một",
    12: "mười hai",
    13: "mười ba",
    14: "mười bốn",
    15: "mười lăm",
    16: "mười sáu",
    17: "mười bảy",
    18: "mười tám",
    19: "mười chín",
    20: "hai mươi",
    21: "hai mươi mốt",
    22: "hai mươi hai",
    23: "hai mươi ba",
    24: "hai mươi bốn",
    25: "hai mươi lăm",
    26: "hai mươi sáu",
    27: "hai mươi bảy",
    28: "hai mươi tám",
    29: "hai mươi chín",
    30: "ba mươi",
}

FROM_VIETNAMESE_ORDINALS_TO_NUMBER = {
    v: k for k, v in FROM_NUMBER_TO_VIETNAMESE_ORDINALS.items()
}

FROM_ROMAN_TO_NUMBER = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
    "XIII": 13,
    "XIV": 14,
    "XV": 15,
    "XVI": 16,
    "XVII": 17,
    "XVIII": 18,
    "XIX": 19,
    "XX": 20,
    "XXI": 21,
    "XXII": 22,
    "XXIII": 23,
    "XXIV": 24,
    "XXV": 25,
    "XXVI": 26,
    "XXVII": 27,
    "XXVIII": 28,
    "XXIX": 29,
    "XXX": 30,
}

FROM_NUMBER_TO_ROMAN = {v: k for k, v in FROM_ROMAN_TO_NUMBER.items()}


# Bảng ánh xạ số La Mã và từ thứ tự tiếng Việt sang số nguyên
VIETNAMESE_ORDINALS = {
    "nhất": 1,
    "thứ nhất": 1,
    "hai": 2,
    "thứ hai": 2,
    "ba": 3,
    "thứ ba": 3,
    "bốn": 4,
    "thứ tư": 4,
    "thứ bốn": 4,
    "tư": 4,
    "năm": 5,
    "thứ năm": 5,
    "sáu": 6,
    "thứ sáu": 6,
    "bảy": 7,
    "thứ bảy": 7,
    "tám": 8,
    "thứ tám": 8,
    "chín": 9,
    "thứ chín": 9,
    "mười": 10,
    "thứ mười": 10,
}


ROMAN_NUMERALS = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
    "XIII": 13,
    "XIV": 14,
    "XV": 15,
    "XVI": 16,
    "XVII": 17,
    "XVIII": 18,
    "XIX": 19,
    "XX": 20,
    "XXI": 21,
    "XXII": 22,
    "XXIII": 23,
    "XXIV": 24,
    "XXV": 25,
    "XXVI": 26,
    "XXVII": 27,
    "XXVIII": 28,
    "XXIX": 29,
    "XXX": 30,
}


class MinimumScoreThresholds:
    """Các ngưỡng điểm tối thiểu cho các loại tìm kiếm khác nhau."""

    SEMANTIC_SEARCH_DOCUMENTS = (
        0.5  # Ngưỡng điểm tối thiểu cho tìm kiếm ngữ nghĩa theo document name
    )

    SEMANTIC_SEARCH_NODES = (
        0.5  # Ngưỡng điểm tối thiểu cho tìm kiếm ngữ nghĩa theo node content
    )


class LegalLabels:
    """Các nhãn (Labels) dùng chung trong Knowledge Graph pháp luật."""

    LegalNode = "LegalNode"


class LegalHierarchyLabels:
    """Nhãn biểu diễn các cấp phân cấp văn bản pháp luật theo cấu trúc cây."""

    Document = "Document"  # Văn bản quy phạm pháp luật (Hiến pháp, Bộ luật, Nghị định, Thông tư...)
    Part = "Part"  # Phần (Phần thứ nhất, Phần thứ hai...)
    Chapter = "Chapter"  # Chương (Chương I, Chương II...)
    Section = "Section"  # Mục (Mục 1, Mục 2...)
    SubSection = "SubSection"  # Tiểu mục (Tiểu mục 1, Tiểu mục 2...)
    Article = "Article"  # Điều (Điều 1, Điều 2...)
    Clause = "Clause"  # Khoản (Khoản 1, Khoản 2...)
    Point = "Point"  # Điểm (Điểm a, Điểm b...)


class LegalRelationshipTypes:
    """Các loại quan hệ (Relationship Types) giữa các node trong Knowledge Graph."""

    CONTAINS = "CONTAINS"  # Quan hệ cấu trúc phân cấp cây (Cha CONTAINS Con)
    REFERENCES = "REFERENCES"  # Quan hệ dẫn chiếu / viện dẫn điều khoản khác
    IMPLEMENTS = "IMPLEMENTS"  # Quan hệ hướng dẫn thi hành (Nghị định -> Luật)
    INTERPRETED_BY = "INTERPRETED_BY"  # Quan hệ giải thích, bổ sung quy định
    AMENDS = "AMENDS"  # Quan hệ sửa đổi, bổ sung quy định
    REPLACES = "REPLACES"  # Quan hệ thay thế quy định
    REPEALS = "REPEALS"  # Quan hệ bãi bỏ quy định
    RELATED_TO = "RELATED_TO"  # Quan hệ liên quan ngữ nghĩa
