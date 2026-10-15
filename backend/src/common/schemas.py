import re
from typing import Optional

from src.common.constants import (
    FROM_ROMAN_TO_NUMBER,
    FROM_VIETNAMESE_ORDINALS_TO_NUMBER,
)
from src.common.custom_exception import CustomException
from src.utils.logger import setup_logger


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
    def __init__(
        self,
        document=None,
        part=None,
        chapter=None,
        section=None,
        subsection=None,
        article=None,
        clause=None,
        point=None,
    ):
        self.document = document
        self.part = part
        self.chapter = chapter
        self.section = section
        self.subsection = subsection
        self.article = article
        self.clause = clause
        self.point = point

    @staticmethod
    def from_dict(data: dict) -> "LegalHierarchy":
        """Tạo một đối tượng LegalHierarchy từ một dict."""

        return LegalHierarchy(
            document=data.get("document", None),
            part=data.get("part", None),
            chapter=data.get("chapter", None),
            section=data.get("section", None),
            subsection=data.get("subsection", None),
            article=data.get("article", None),
            clause=data.get("clause", None),
            point=data.get("point", None),
        )

    def to_dict(self):
        """Chuyển đổi đối tượng LegalHierarchy thành dict."""
        return {
            "document": self.document,
            "part": self.part,
            "chapter": self.chapter,
            "section": self.section,
            "subsection": self.subsection,
            "article": self.article,
            "clause": self.clause,
            "point": self.point,
        }

    @staticmethod
    def from_ancestors(ancestors: list[dict]) -> "LegalHierarchy":
        """Tạo LegalHierarchy từ chuỗi tổ tiên (breadcrumb) đọc từ đồ thị.

        Mỗi phần tử trong `ancestors` cần có `labels` (nhãn node) và `number`
        (riêng `Document` dùng `title`). Loại node được suy ra từ **label** vì
        graph không lưu `type` dưới dạng property.

        Args:
            ancestors: Danh sách node theo thứ tự Document -> ... -> node hiện tại.

        Returns:
            LegalHierarchy: Đối tượng phân cấp dựng từ phả hệ đồ thị.
        """
        field_by_label = {
            "Document": "document",
            "Part": "part",
            "Chapter": "chapter",
            "Section": "section",
            "SubSection": "subsection",
            "Article": "article",
            "Clause": "clause",
            "Point": "point",
        }
        values = {field: None for field in field_by_label.values()}

        for node in ancestors or []:
            labels = [
                label for label in (node.get("labels") or []) if label != "LegalNode"
            ]
            node_label = next(
                (label for label in labels if label in field_by_label), None
            )
            if not node_label:
                continue

            field = field_by_label[node_label]
            if field == "document":
                values[field] = node.get("title") or node.get("node_id")
            else:
                values[field] = node.get("number")

        return LegalHierarchy.from_dict(values)

    def has_any_hierarchy(self) -> bool:
        """Kiểm tra xem có bất kỳ cấp nào trong phân cấp pháp lý được xác định hay không."""
        return any(
            getattr(self, field) is not None
            for field in [
                "document",
                "part",
                "chapter",
                "section",
                "subsection",
                "article",
                "clause",
                "point",
            ]
        )

    def get_all_info(self) -> dict:
        """Trả về tất cả thông tin phân cấp và các thông tin để tạo node"""
        res = {
            "hierarchy": self.to_dict(),
            "node_type": self.get_node_type(),
            "parent_node_type": self.get_parent_node_type(),
            "citation_path": self.get_citation_path(),
            "postfix_node_id": self.get_postfix_node_id(),
        }
        return res

    def validate(self, require_document: bool) -> tuple[bool, Optional[str]]:
        """Kiểm tra cấu trúc hợp lệ của các thành phần trong phân cấp pháp lý.

        Thứ tự phân cấp từ lớn đến nhỏ:
        document > part > chapter > section > subsection > article > clause > point

        Quy tắc:
        - Các cấp Phần, Chương, Mục, Tiểu mục, Khoản, Điểm có thể không tồn tại.
        - Không thể có Khoản hoặc Điểm khi không có Điều.
        - Cấp con chỉ hợp lệ khi tồn tại cấp cha tương ứng.

        Các mô hình sắp xếp phổ biến được pháp luật cho phép:
        Phần -> Chương -> Mục -> Tiểu mục -> Điều -> Khoản -> Điểm
        Phần -> Chương -> Mục -> Điều -> Khoản -> Điểm
        Chương -> Mục -> Tiểu mục -> Điều -> Khoản -> Điểm
        Chương -> Mục -> Điều -> Khoản -> Điểm
        Chương -> Điều -> Khoản -> Điểm
        Điều -> Khoản -> Điểm

        Args:
            require_document (bool): Bắt buộc phải có `document` hay không.

        Returns:
            tuple[bool, Optional[str]]: (True, None) nếu hợp lệ; ngược lại (False, thông báo lỗi).
        """

        if require_document is None:
            return False, "require_document không thể là None."

        if require_document and not self.document:
            return False, "Văn bản pháp luật không thể trống."

        if self.section and not self.chapter:
            return False, "Mục không thể tồn tại nếu không có Chương."

        if self.subsection and not self.section:
            return False, "Tiểu mục không thể tồn tại nếu không có Mục."

        if self.clause and not self.article:
            return False, "Khoản không thể tồn tại nếu không có Điều."

        if self.point and not self.clause:
            return False, "Điểm không thể tồn tại nếu không có Khoản."

        return True, None

    def get_node_type(self) -> str:
        """Xác định loại node dựa trên các cấp hiện có trong phân cấp pháp lý.

        Raises:
            CustomException: Lỗi nếu không có cấu trúc

        Returns:
            str: Loại node (Document, Part, Chapter, Section, SubSection, Article, Clause, Point)
        """
        if self.point is not None:
            return "Point"
        elif self.clause is not None:
            return "Clause"
        elif self.article is not None:
            return "Article"
        elif self.subsection is not None:
            return "SubSection"
        elif self.section is not None:
            return "Section"
        elif self.chapter is not None:
            return "Chapter"
        elif self.part is not None:
            return "Part"
        elif self.document is not None:
            return "Document"

        raise CustomException("Không xác định được loại node từ phân cấp pháp lý.")

    def get_parent_node_type(self) -> str:
        """Xác định loại node cha dựa trên các cấp hiện có trong phân cấp pháp lý.
        Node cha gần nhất khác None sẽ được coi là node cha của node hiện tại.

        Raises:
            CustomException: Lỗi nếu không có cấu trúc

        Returns:
            str: Loại node cha (Document, Part, Chapter, Section, SubSection, Article, Clause)
        """

        # Nếu là document thì không có node cha
        if self.get_node_type() == "Document":
            return None

        types = [
            "Point",
            "Clause",
            "Article",
            "SubSection",
            "Section",
            "Chapter",
            "Part",
            "Document",
        ]
        node_type = self.get_node_type()

        index = types.index(node_type)

        for i in range(index + 1, len(types)):
            parent_type = types[i]
            if getattr(self, parent_type.lower()) is not None:
                return parent_type

        return "Document"  # Nếu không có cấp cha nào khác, coi Document là cha.

    def get_citation_path(self, separator: str = " ") -> str:
        """Chuyển đổi phân cấp pháp lý thành đường dẫn trích dẫn.
        Từ cấp nhỏ đến cấp lớn: Điểm -> Khoản -> Điều -> Tiểu mục -> Mục -> Chương -> Phần và tài liệu pháp luật (document).

        Args:
            separator (str): Ký tự phân tách giữa các phần. Mặc định là khoảng trắng.

        Returns:
            str: Đường dẫn trích dẫn. Ví dụ: Điểm a Khoản 1 Điều 24 Tiểu mục 1 Mục 1 Chương III Phần I của Nghị quyết số 351/2017/UBTVQH14
        """
        parts = []
        if self.point is not None:
            parts.append(f"Điểm {self.point}")
        if self.clause is not None:
            parts.append(f"Khoản {self.clause}")
        if self.article is not None:
            parts.append(f"Điều {self.article}")
        if self.subsection is not None:
            parts.append(f"Tiểu mục {self.subsection}")
        if self.section is not None:
            parts.append(f"Mục {self.section}")
        if self.chapter is not None:
            parts.append(f"Chương {self.chapter}")
        if self.part is not None:
            parts.append(f"Phần {self.part}")

        path = separator.join(parts)
        if self.document:
            path = f"{path} của {self.document}" if path else str(self.document)
        return path

    def get_postfix_node_id(self) -> str:
        """Chuyển đổi phân cấp pháp lý thành ID chuẩn hóa theo định dạng postfix.

        Returns:
            str: _P1_CH1_M1_TM1_D1_K1_DIEM_A
        """
        return self.get_node_id_from_document_id("")

    def get_node_id_from_document_id(self, document_id: str) -> str:
        """Chuyển đổi phân cấp pháp lý thành ID chuẩn hóa dựa trên loại node và ngữ cảnh cha con.


        Args:
            document_id (str): document ID (ví dụ: 351_2017_UBTVQH14) có thể rỗng

        Raises:
            CustomException: Nếu document_id là None hoặc nếu loại node là Document (không thể tự tạo ID cho Document).

        Returns:
            str: ID chuẩn hóa của node. Ví dụ: HIENPHAP_2013_P1_CH1_M1_TM1_D1_K1_DIEM_A
        """

        if document_id is None:
            raise CustomException("document_id không thể là None.", status_code=400)

        type_node = self.get_node_type()

        if type_node == "Document":
            raise CustomException(
                f"Không thể tự tạo ID cho node Document. Tên văn bản: {self.document}",
                status_code=400,
            )

        # Chuyến các Part, Chapter, Section, Subsection, Article, Clause, thành số nguyên
        def normalize_number(value):
            if value is None:
                return None

            if isinstance(value, int):
                return value

            val_str = str(value).strip()
            if val_str.isdigit():
                return int(val_str)

            if isinstance(val_str, str):
                if val_str in FROM_ROMAN_TO_NUMBER:
                    return FROM_ROMAN_TO_NUMBER[val_str]

                if val_str in FROM_VIETNAMESE_ORDINALS_TO_NUMBER:
                    return FROM_VIETNAMESE_ORDINALS_TO_NUMBER[val_str]

            return val_str

        part_num = normalize_number(self.part)
        chapter_num = normalize_number(self.chapter)
        section_num = normalize_number(self.section)
        subsection_num = normalize_number(self.subsection)
        article_num = normalize_number(self.article)
        clause_num = normalize_number(self.clause)

        if type_node == "Part":
            return f"{document_id}_P{part_num}"
        elif type_node == "Chapter":
            part_prefix = f"_P{part_num}" if part_num else ""
            return f"{document_id}{part_prefix}_CH{chapter_num}"
        elif type_node == "Section":
            ch_prefix = f"_CH{chapter_num}" if chapter_num else ""
            return f"{document_id}{ch_prefix}_M{section_num}"
        elif type_node == "Subsection":
            ch_prefix = f"_CH{chapter_num}" if chapter_num else ""
            m_prefix = f"_M{section_num}" if section_num else ""
            return f"{document_id}{ch_prefix}{m_prefix}_TM{subsection_num}"
        elif type_node == "Article":
            return f"{document_id}_D{article_num}"
        elif type_node == "Clause":
            return f"{document_id}_D{article_num}_K{clause_num}"
        elif type_node == "Point":
            if self.clause:
                return f"{document_id}_D{self.article}_K{self.clause}_DIEM_{self.point.upper()}"
            else:
                return f"{document_id}_D{self.article}_DIEM_{self.point.upper()}"

        return f"{document_id}_{type_node.upper()}_{self.get_node_type()}"
