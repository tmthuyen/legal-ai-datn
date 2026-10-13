
from src.common.custom_exception import CustomException
from src.common.schemas import LegalHierarchy, LegalHierarchyPatterns



class ExtractorLegalQuery:
    def __init__(self):
        pass

    def extract(self, query_text: str, document: str) -> dict:
        """ Trích xuất phân cấp luật từ câu truy vấn và tên văn bản pháp luật.
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
                "hierarchy": dict,  # Phân cấp luật được trích xuất từ câu truy vấn, có cả văn bản.
            }
        """
        query_text = query_text.strip()
        document = document.strip()

        if not query_text:
            raise CustomException("Câu truy vấn không được để trống.")

        if not document:
            raise CustomException("Tên văn bản pháp luật không được để trống.")

        # Trích xuất các cấp cấu trúc từ câu truy vấn.
        values = {}

        for field, pattern in LegalHierarchyPatterns.hierarchy_patterns.items():
            match = pattern.search(query_text)
            values[field] = match.group(1) if match else None

        # Chuẩn hóa các giá trị không phân biệt hoa/thường.
        for field in ("point", "part", "chapter", "section", "subsection"):
            if values[field] is not None:
                values[field] = values[field].lower()

        # Xây dựng và kiểm tra cấu trúc phân cấp.
        hierarchy = LegalHierarchy()
        hierarchy.document = document

        for field, value in values.items():
            setattr(hierarchy, field, value)

        hierarchy.validate()

        # Trả về dữ liệu làm dataset.
        return {
            "query_text": query_text,
            "hierarchy": hierarchy.to_dict(),
        }