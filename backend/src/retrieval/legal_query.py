
from src.common.custom_exception import CustomException
from src.common.schemas import LegalHierarchy, LegalHierarchyPatterns



class ExtractorLegalQuery:
    def __init__(self):
        pass

    def extract(self, query_text: str, document: str) -> dict:
        query_text = query_text.strip()
        document = document.strip()

        if not query_text:
            raise CustomException("Câu truy vấn không được để trống.")

        if not document:
            raise CustomException("Tên văn bản pháp luật không được để trống.")

        # 1. Trích xuất các cấp cấu trúc từ câu truy vấn.
        values = {}

        for field, pattern in LegalHierarchyPatterns.hierarchy_patterns.items():
            match = pattern.search(query_text)
            values[field] = match.group(1) if match else None

        # 2. Chuẩn hóa các giá trị không phân biệt hoa/thường.
        for field in ("point", "part", "chapter", "section", "subsection"):
            if values[field] is not None:
                values[field] = values[field].lower()

        # 3. Loại bỏ các thành phần dẫn chiếu để lấy nội dung câu hỏi.
        question_text = query_text

        # Xóa các cụm dẫn chiếu như:
        # "Theo", "Tìm hiểu", "tại", "ở", "về" không được xóa tùy tiện
        # vì có thể là nội dung thực sự của câu hỏi.
        for pattern in LegalHierarchyPatterns.hierarchy_patterns.values():
            question_text = pattern.sub("", question_text)

        # Loại bỏ các cụm mở đầu thường gặp.
        question_text = LegalHierarchyPatterns.query_prefix_pattern.sub(
            "", question_text
        )

        # Chuẩn hóa khoảng trắng và dấu câu ở đầu/cuối.
        question_text = " ".join(question_text.split())
        question_text = question_text.strip(" ,:;.-")

        if not question_text:
            raise CustomException(
                "Câu truy vấn không chứa thông tin câu hỏi."
            )

        # 4. Xây dựng và kiểm tra cấu trúc phân cấp.
        hierarchy = LegalHierarchy()
        hierarchy.document = document

        for field, value in values.items():
            setattr(hierarchy, field, value)

        hierarchy.validate()

        # 5. Trả về dữ liệu làm dataset.
        return {
            "query_text": query_text,
            "question_text": question_text,
            "context": hierarchy.to_dict(),
        }