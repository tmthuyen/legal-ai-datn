import re

from src.common.custom_exception import CustomException


class LegalHierarchyPatterns:
    query_prefix_pattern = re.compile(
        r"^\s*(?:"
        r"theo|"
        r"tìm\s+hiểu|"
        r"cho\s+hỏi|"
        r"hãy\s+cho\s+biết|"
        r"vui\s+lòng\s+cho\s+biết"
        r")\b\s*",
        re.IGNORECASE,
    )

    hierarchy_patterns = {
        "point": re.compile(
            r"\bĐiểm\s+([a-z])\b",
            re.IGNORECASE,
        ),
        "clause": re.compile(
            r"\bKhoản\s+(\d+)\b",
            re.IGNORECASE,
        ),
        "article": re.compile(
            r"\bĐiều\s+(\d+[a-z]?)\b",
            re.IGNORECASE,
        ),
        "subsection": re.compile(
            r"\bTiểu\s+mục\s+(\d+|[IVXLCDM]+)\b",
            re.IGNORECASE,
        ),
        "section": re.compile(
            r"\bMục\s+(\d+|[IVXLCDM]+)\b",
            re.IGNORECASE,
        ),
        "chapter": re.compile(
            r"\bChương\s+(\d+|[IVXLCDM]+)\b",
            re.IGNORECASE,
        ),
        "part": re.compile(
            r"\bPhần\s+(?:thứ\s+)?"
            r"(\d+|[IVXLCDM]+|nhất|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười)\b",
            re.IGNORECASE,
        ),
    }

class LegalHierarchy:
    def __init__(self, 
                 document=None, 
                 part=None, 
                chapter=None,
                 section=None, 
                 subsection=None, 
                 article=None, 
                 clause=None, 
                 point=None):
        self.document = document
        self.part = part
        self.chapter = chapter
        self.section = section
        self.subsection = subsection
        self.article = article
        self.clause = clause
        self.point = point
        
    def to_dict(self):
        return {
            "document": self.document,
            "part": self.part,
            "chapter": self.chapter,
            "section": self.section,
            "subsection": self.subsection,
            "article": self.article,
            "clause": self.clause,
            "point": self.point
        }
        
        
    def validate(self) -> bool:
        """Kiểm tra cấu trúc hợp lệ của các thành phần trong phân cấp pháp lý.
            Theo thứ tự lớn đến nhỏ: document > part > section > subsection > article > clause > point
            Nếu có cấp cha không tồn tại nhưng có cấp con thì vẫn hợp lệ
            Có thể không có các cấp: Phần, Mục, Tiểu mục, Khoản, Điểm
            Không thể không có Điều nhưng có Khoản hoặc Điểm      
            
            Các mô hình sắp xếp phổ biến được pháp luật cho phép:
            Phần -> Chương -> Mục -> Tiểu mục -> Điều -> Khoản -> Điểm
            Phần -> Chương -> Mục -> Điều -> Khoản -> Điểm
            Chương -> Mục -> Tiểu mục -> Điều -> Khoản -> Điểm
            Chương -> Mục -> Điều -> Khoản -> Điểm
            Chương -> Điều -> Khoản -> Điểm
            Điều -> Khoản -> Điểm
        """
        
        if not self.document:
            raise CustomException("Văn bản pháp luật không thể trống.") 
        
        if self.point and not self.clause:
            raise CustomException("Điểm không thể tồn tại nếu không có Khoản.")
        
        if self.clause and not self.article:
            raise CustomException("Khoản không thể tồn tại nếu không có Điều.")
        
        if self.subsection and not self.section:
            raise CustomException("Tiểu mục không thể tồn tại nếu không có Mục.")
        
        return True