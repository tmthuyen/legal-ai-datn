from src.common.constants import (
    FROM_NUMBER_TO_ROMAN,
    FROM_NUMBER_TO_VIETNAMESE_ORDINALS,
)
from src.common.custom_exception import CustomException
from src.common.schemas import LegalHierarchy, LegalHierarchyPatterns
from src.utils.logger import setup_logger

logger = setup_logger("legal_query_extractor", "legal_query_extractor.log")


class LegalQueryExtractor:
    def __init__(self):
        pass

    def extract_hierarchy(self, query_text: str, document: str = None) -> dict:
        """Trích xuất phân cấp luật từ câu truy vấn và tên văn bản pháp luật.
        - Chỉ trích xuât các cấp: Phần, Chương, Mục, Tiểu mục, Điều, Khoản, Điểm
        - Chưa có khả năng trích văn bản được nhắc đên trong câu truy vấn
        - Dùng làm output để fine-tune mô hình có khả năng trích xuất phân cấp luật và cả văn bản (document) từ câu truy vấn.

        Args:
            query_text (str): Câu truy vấn từ người dùng (Có chứa vị trí trích dẫn).
            document (str): Tên văn bản pháp luật.

        Raises:
            - CustomException: Nếu câu truy vấn hoặc tên văn bản pháp luật bị để trống.
            - Nếu phân cấp không hợp lệ thì báo lỗi

        Returns:
            dict:
            {
                "query_text": str,  # Câu truy vấn ban đầu từ người dùng.
                "hierarchy": {
                    "document": str, # str
                    "part": str,          # str: thứ nhất
                    "chapter": str,       # str: I, II, III
                    "section": number,       # number: 1, 2, 3
                    "subsection": number,    # number: 1, 2, 3
                    "article": number,       # number: 1, 2, 3
                    "clause": number,        # number: 1, 2, 3
                    "point": str          # str: a, b, c
                },
                "has_hierarchy": bool,  # True nếu có phân cấp, False nếu không có phân cấp
                "valid_hierarchy": bool  # True nếu phân cấp hợp lệ, False nếu không hợp lệ
            }
        """
        logger.info(
            f"Extracting hierarchy from query: '{query_text}' with document: '{document}'."
        )

        query_text = query_text.strip()
        if document is not None:
            document = document.strip()

            if document == "":
                raise CustomException("Tên văn bản pháp luật không được để trống.")

        if not query_text:
            raise CustomException("Câu truy vấn không được để trống.")

        # Trích xuất các cấp cấu trúc từ câu truy vấn.
        # điểm a khoản 1 Điều 24 Tiểu mục 1 Mục 1 Chương III Phần I của Nghị quyết số 351/2017/UBTVQH14.
        values = {
            "document": document,  # str
            "part": None,  # str: thứ nhất
            "chapter": None,  # str: I, II, III
            "section": None,  # number: 1, 2, 3
            "subsection": None,  # number: 1, 2, 3
            "article": None,  # number: 1, 2, 3
            "clause": None,  # number: 1, 2, 3
            "point": None,  # str: a, b, c
        }

        for field, pattern in LegalHierarchyPatterns.hierarchy_patterns.items():
            match = pattern.search(query_text)
            values[field] = match.group(1) if match else None

        # Chuẩn hóa các giá trị không phân biệt hoa/thường.
        values["point"] = values["point"].lower() if values["point"] else None

        # Xử lý phần: số 1, 2 hoặc số la mã I, II sang thứ tự tiếng Việt: nhất, hai, ba, bốn, năm, sáu, bảy, tám, chín, mười
        values["part"] = FROM_NUMBER_TO_VIETNAMESE_ORDINALS.get(
            values["part"], values["part"]
        )

        # Xử lý chương: số 1, 2 sang la mã
        values["chapter"] = FROM_NUMBER_TO_ROMAN.get(
            values["chapter"], values["chapter"]
        )

        # Xây dựng và kiểm tra cấu trúc phân cấp.
        hierarchy = LegalHierarchy.from_dict(values)

        is_valid = None
        error_message = None
        if document is not None:
            hierarchy.document = document
            is_valid, error_message = hierarchy.validate(require_document=True)
        else:
            is_valid, error_message = hierarchy.validate(require_document=False)

        if not is_valid:
            logger.error(f"Phân cấp không hợp lệ: {error_message}")

        # Trả về dữ liệu làm dataset.
        return {
            "query_text": query_text,
            "hierarchy": hierarchy.to_dict(),
            "has_hierarchy": hierarchy.has_any_hierarchy(),
            "valid_hierarchy": is_valid,
        }

    def extract_hierarchy_with_model(self, query_text: str) -> dict:
        """Sử dụng fine tune model để trích xuất phân cấp

        Args:
            query_text (str): truy vấn người dùng

        Returns:
            dict: {
                "query_text": str,  # Câu truy vấn ban đầu từ người dùng.
                "hierarchy": {
                    "document": str, # str
                    "part": str,          # str: thứ nhất
                    "chapter": str,       # str: I, II, III
                    "section": number,       # number: 1, 2, 3
                    "subsection": number,    # number: 1, 2, 3
                    "article": number,       # number: 1, 2, 3
                    "clause": number,        # number: 1, 2, 3
                    "point": str          # str: a, b, c
                },
                "has_hierarchy": bool,  # True nếu có phân cấp, False nếu không có phân cấp
                "valid_hierarchy": bool  # True nếu phân cấp hợp lệ, False nếu không hợp lệ
            }
        """

        logger.info(f"Extracting hierarchy from query: '{query_text}' using model.")

        # load model

        # run model

        # xử lý kết quả
        extracted_hierarchy = {
            "document": "Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013",  # str document do model tách ra
            "part": None,  # str: thứ nhất
            "chapter": None,  # str: I, II, III
            "section": None,  # number: 1, 2, 3
            "subsection": None,  # number: 1, 2, 3
            "article": None,  # number: 1, 2, 3
            "clause": None,  # number: 1, 2, 3
            "point": None,  # str: a, b, c
        }

        hierarchy = LegalHierarchy.from_dict(extracted_hierarchy)
        is_valid, error_message = hierarchy.validate(require_document=True)

        if not is_valid:
            logger.error(f"Phân cấp không hợp lệ: {error_message}")

        return {
            "query_text": query_text,
            "hierarchy": hierarchy.to_dict(),
            "has_hierarchy": hierarchy.has_any_hierarchy(),
            "valid_hierarchy": is_valid,
        }
