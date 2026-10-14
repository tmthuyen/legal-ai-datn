"""
graph_service.py
Service layer xử lý nghiệp vụ truy vấn Knowledge Graph pháp luật Việt Nam.
Cung cấp dữ liệu ngữ cảnh phân cấp, quan hệ pháp lý và xuất xứ phục vụ cho AI suy luận.
"""

from typing import Any, Optional

from src.common.schemas import LegalHierarchy
from src.graph.graph_repository import (
    LegalGraphRepository,
    LegalLabels,
    LegalRelationshipTypes,
)
from src.utils.logger import setup_logger

logger = setup_logger(name="graph_service", filename="graph_service.log")


class LegalGraphService:
    """
    Service layer chịu trách nhiệm:
    - Điều phối các truy vấn đồ thị từ repository.
    - Phân giải mục tiêu trích dẫn (Target Resolution) xuống node đồ thị cụ thể.
    - Truy xuất cây phân cấp (Breadcrumb / Children / Descendants).
    - Khai thác mạng lưới quan hệ pháp lý (REFERENCES, IMPLEMENTS...).
    - Đóng gói trọn vẹn ngữ cảnh truy xuất (Retrieval Context) làm đầu vào cho AI suy luận.
    """

    def __init__(self, repository: LegalGraphRepository):
        """
        Khởi tạo LegalGraphService với một repository instance.
        
        Args:
            repository: Đối tượng LegalGraphRepository đã kết nối Neo4jClient.
        """
        self._repository = repository

    @property
    def repository(self) -> LegalGraphRepository:
        """Truy cập đối tượng repository."""
        return self._repository

    # --------------------------------------------------------------------------
    # 1. TRUY VẤN NODE & VĂN BẢN
    # --------------------------------------------------------------------------

    def get_node_by_id(self, node_id: str) -> Optional[dict[str, Any]]:
        """
        Lấy thông tin chi tiết của một node trong đồ thị theo node_id.
        
        Args:
            node_id: Mã định danh node (ví dụ: 'HIEN_PHAP_2013_D1', 'BLDS_2015_D27_K1_DIEM_A').
            
        Returns:
            Dict thuộc tính node hoặc None nếu không tìm thấy.
        """
        if not node_id:
            logger.warning("node_id rỗng.")
            return None
        return self._repository.find_node_by_id(node_id)

    def get_document(self, document_id: str) -> Optional[dict[str, Any]]:
        """
        Lấy thông tin văn bản quy phạm pháp luật theo document_id.
        
        Args:
            document_id: Mã định danh văn bản (ví dụ: 'HIEN_PHAP_2013', 'BLDS_2015').
            
        Returns:
            Dict metadata của văn bản hoặc None.
        """
        if not document_id:
            return None
        return self._repository.find_document_by_id(document_id)

    def get_all_documents(self) -> list[dict[str, Any]]:
        """
        Lấy danh sách tất cả các văn bản quy phạm pháp luật hiện có trong đồ thị.
        
        Returns:
            Danh sách các Document node.
        """
        return self._repository.get_all_documents()

    # --------------------------------------------------------------------------
    # 2. PHÂN GIẢI TRÍCH DẪN MỤC TIÊU (TARGET RESOLUTION)
    # --------------------------------------------------------------------------

    def resolve_target_node(
        self,
        document_id: str,
        target: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """
        Phân giải cấu trúc target (trích xuất từ câu hỏi người dùng) thành node đích thực tế trên đồ thị.
        
        Cấu trúc target mẫu:
        {
            "part": None,
            "chapter": "I",
            "section": None,
            "subsection": None,
            "article": "1",
            "clause": None,
            "point": None,
            "document": "Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013"
        }
        
        Args:
            document_id: Mã văn bản đã được chuẩn hóa (ví dụ 'HIEN_PHAP_2013', 'BLDS_2015').
            target: Dict chứa các trường phân cấp trích dẫn.
            
        Returns:
            Dict node đích sâu nhất tìm thấy trên đồ thị, hoặc None nếu không tồn tại.
        """
        if not document_id:
            logger.error("Không có document_id để phân giải target.")
            return None

        part = target.get("part")
        chapter = target.get("chapter")
        section = target.get("section")
        subsection = target.get("subsection")
        article = target.get("article")
        clause = target.get("clause")
        point = target.get("point")

        return self._repository.find_node_by_hierarchy(
            document_id=document_id,
            part=part,
            chapter=chapter,
            section=section,
            subsection=subsection,
            article=article,
            clause=clause,
            point=point,
        )

    # --------------------------------------------------------------------------
    # 3. TRUY VẤN PHẢ HỆ VÀ CÂY NỘI DUNG (BREADCRUMB & CONTENT TREE)
    # --------------------------------------------------------------------------

    def get_breadcrumbs(self, node_id: str) -> list[dict[str, Any]]:
        """
        Lấy chuỗi phả hệ tổ tiên (Breadcrumbs) từ văn bản gốc tới node hiện tại.
        
        Ví dụ: Document -> Chapter -> Article -> Clause -> Point.
        
        Args:
            node_id: Mã định danh node.
            
        Returns:
            Danh sách tóm tắt từng cấp trên đường dẫn phả hệ.
        """
        if not node_id:
            return []
        return self._repository.get_ancestors(node_id)

    def get_children(self, node_id: str) -> list[dict[str, Any]]:
        """
        Lấy danh sách các node con trực tiếp của node hiện tại.
        
        Args:
            node_id: Mã định danh node cha.
            
        Returns:
            Danh sách node con (ví dụ các Khoản thuộc Điều, hoặc các Điều thuộc Chương).
        """
        if not node_id:
            return []
        return self._repository.get_children(node_id)

    def get_descendants(
        self,
        node_id: str,
        max_depth: int = 5,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """
        Lấy toàn bộ cây node con cháu bên dưới node hiện tại đến độ sâu max_depth.
        
        Args:
            node_id: Mã node gốc.
            max_depth: Độ sâu duyệt cây.
            limit: Giới hạn số lượng node.
            
        Returns:
            Danh sách các node hậu duệ kèm thông tin độ sâu (depth).
        """
        if not node_id:
            return []
        return self._repository.get_descendants(node_id, max_depth=max_depth, limit=limit)

    def get_node_content_and_hierarchy(self, node_id: str) -> Optional[dict[str, Any]]:
        """
        Lấy trọn vẹn nội dung của node cùng danh sách các node con trực thuộc để xây dựng ngữ cảnh quy phạm.
        
        Args:
            node_id: Mã node cần lấy nội dung.
            
        Returns:
            Dict gồm:
            - node: thông tin node hiện tại (title, text, full_text, number...)
            - breadcrumbs: phả hệ tổ tiên
            - children: danh sách con trực tiếp
        """
        node = self.get_node_by_id(node_id)
        if not node:
            return None

        breadcrumbs = self.get_breadcrumbs(node_id)
        children = self.get_children(node_id)

        return {
            "node": node,
            "breadcrumbs": breadcrumbs,
            "children": children,
        }

    def get_citation_path(self, node_id: str) -> Optional[str]:
        """
        Truy vết và trả về trích dẫn tuyệt đối (citation path) của một node bất kỳ trên đồ thị.

        Quy trình:
        1. Lấy chuỗi tổ tiên Document -> ... -> node qua `get_breadcrumbs` (quan hệ CONTAINS).
        2. Dựng lại `LegalHierarchy` từ phả hệ (suy loại node từ **label**, không đọc property `type`).
        3. Tái sử dụng `LegalHierarchy.get_citation_path()` để sinh chuỗi trích dẫn (thứ tự nhỏ -> lớn).

        Args:
            node_id: Mã định danh node cần lấy trích dẫn.

        Returns:
            str: Trích dẫn tuyệt đối, ví dụ
            'Điểm a Khoản 1 Điều 522 của Bộ luật Dân sự 2015'; hoặc None nếu không tìm thấy node.
        """
        if not node_id:
            return None

        breadcrumbs = self.get_breadcrumbs(node_id)
        if not breadcrumbs:
            logger.warning(f"Không lấy được phả hệ để dựng trích dẫn cho node='{node_id}'.")
            return None

        return LegalHierarchy.from_ancestors(breadcrumbs).get_citation_path()

    # --------------------------------------------------------------------------
    # 4. TRUY VẤN MẠNG LƯỚI QUAN HỆ PHÁP LÝ (LEGAL RELATIONSHIPS)
    # --------------------------------------------------------------------------

    def get_related_laws(
        self,
        node_id: str,
        relation_types: Optional[list[str]] = None,
        hops: int = 1,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Truy xuất các quy định, văn bản pháp luật có mối liên hệ pháp lý với node hiện tại
        (như dẫn chiếu REFERENCES, hướng dẫn thi hành IMPLEMENTS, giải thích INTERPRETED_BY).
        
        Args:
            node_id: Mã node nguồn.
            relation_types: Danh sách loại quan hệ cần lấy (mặc định lấy tất cả trừ CONTAINS).
            hops: Số bước nhảy (1 hoặc 2 hop).
            limit: Số lượng tối đa.
            
        Returns:
            Danh sách các node và quan hệ liên quan.
        """
        if not node_id:
            return []

        if hops == 1 and not relation_types:
            # Lấy chi tiết cả quan hệ đi ra và đi vào kèm thuộc tính (evidence, confidence)
            return self._repository.get_all_node_relationships(node_id, limit=limit)

        return self._repository.get_related_legal_nodes(node_id, hops=hops, limit=limit)

    # --------------------------------------------------------------------------
    # 5. XUẤT XỨ & HIỆU LỰC TÀI LIỆU (PROVENANCE & ANTI-HALLUCINATION)
    # --------------------------------------------------------------------------

    def get_document_provenance(self, document_id_or_node_id: str) -> Optional[dict[str, Any]]:
        """
        Lấy thông tin xuất xứ pháp lý, số hiệu, ngày ban hành và tình trạng hiệu lực
        từ node :Document để kiểm chứng chống bịa đặt (Anti-hallucination).
        
        Args:
            document_id_or_node_id: Có thể là document_id ('HIEN_PHAP_2013') hoặc node_id ('BLDS_2015_D27').
            
        Returns:
            Dict chứa metadata nguồn gốc văn bản.
        """
        if not document_id_or_node_id:
            return None

        # Thử lấy trực tiếp theo document_id
        prov = self._repository.get_document_provenance(document_id_or_node_id)
        if prov:
            return prov

        # Nếu không được, truy ngược qua node_id
        return self._repository.get_node_provenance(document_id_or_node_id)

    # --------------------------------------------------------------------------
    # 6. ĐÓNG GÓI NGỮ CẢNH TRUY XUẤT TOÀN DIỆN CHO AI SUY LUẬN (RETRIEVAL ORCHESTRATION)
    # --------------------------------------------------------------------------

    def get_full_retrieval_context(
        self,
        document_id: str,
        target: dict[str, Any],
        query_text: str = "", 
    ) -> dict[str, Any]:
        """
        Đóng gói toàn diện kết quả truy xuất (Retrieval Result) từ câu hỏi và mục tiêu trích dẫn,
        tạo thành input hoàn chỉnh đưa vào module AI suy luận (Reasoning / LLM).
        
        Quy trình thực hiện:
        1. Phân giải target thành node đích cụ thể trên đồ thị.
        2. Lấy phả hệ tổ tiên (Breadcrumbs).
        3. Lấy nội dung chi tiết của node (text, full_text) và các node con trực tiếp.
        4. Truy vết các quan hệ pháp lý và quy định liên quan (REFERENCES, IMPLEMENTS...).
        5. Lấy xuất xứ văn bản gốc (Provenance: số hiệu, hiệu lực, file nguồn).
        
        Args:
            document_id: Mã văn bản đã chuẩn hóa.
            target: Dict mục tiêu trích dẫn phân cấp.
            query_text: Câu truy vấn gốc của người dùng.
            question_text: Nội dung câu hỏi sau khi lược bỏ trích dẫn.
            
        Returns:
            Dict kết quả chuẩn cấu trúc RetrievalResult.
        """
        logger.info(f"Bắt đầu đóng gói ngữ cảnh truy xuất cho document='{document_id}'...")

        # 1. Phân giải node
        resolved_node = self.resolve_target_node(document_id, target)
        if not resolved_node:
            logger.warning(f"Không thể phân giải node cho target={target} trong document='{document_id}'.")
            provenance = self.get_document_provenance(document_id)
            return {
                "query_info": {
                    "query_text": query_text, 
                },
                "resolved": None,
                "content": None,
                "related": [],
                "provenance": provenance,
                "status": "TARGET_NOT_FOUND",
            }

        target_node_id = resolved_node["node_id"]

        # 2. Phả hệ (Breadcrumbs)
        breadcrumbs = self.get_breadcrumbs(target_node_id)

        # 3. Nội dung & Node con
        children = self.get_children(target_node_id)
        content_info = {
            "node_id": target_node_id,
            "type": resolved_node.get("type"),
            "title": resolved_node.get("title"),
            "number": resolved_node.get("number"),
            "text": resolved_node.get("text"),
            "full_text": resolved_node.get("full_text"),
            "children": [
                {
                    "node_id": c.get("node_id"),
                    "type": c.get("type"),
                    "number": c.get("number"),
                    "title": c.get("title"),
                    "text": c.get("text"),
                }
                for c in children
            ],
        }

        # 4. Quan hệ pháp lý liên quan (1-hop)
        related_laws = self.get_related_laws(target_node_id, limit=30)

        # 5. Xuất xứ văn bản (Provenance)
        provenance = self.get_document_provenance(target_node_id) or self.get_document_provenance(document_id)

        logger.info(f"Đóng gói hoàn tất ngữ cảnh truy xuất cho node='{target_node_id}'.")

        return {
            "query_info": {
                "query_text": query_text, 
            },
            "resolved": {
                "document_id": document_id,
                "node_id": target_node_id,
                "type": resolved_node.get("type"),
                "breadcrumb": breadcrumbs,
            },
            "content": content_info,
            "related": related_laws,
            "provenance": provenance,
            "status": "SUCCESS",
        }

    # --------------------------------------------------------------------------
    # 7. CÁC HÀM TIỆN ÍCH & TƯƠNG THÍCH CŨ
    # --------------------------------------------------------------------------

    def get_all_legal_nodes(
        self,
        limit: int = 100,
        order_by: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Lấy tất cả các LegalNode trong đồ thị (phục vụ kiểm tra/test)."""
        return self._repository.find_all(
            label=LegalLabels.LegalNode,
            limit=limit,
            order_by=order_by,
        )

    def get_all_legal_relationships(self, limit: int = 100) -> list[dict[str, Any]]:
        """Lấy tất cả các quan hệ trong đồ thị."""
        return self._repository.get_all_relationships(
            label=LegalLabels.LegalNode,
            limit=limit,
        )

    def get_relationships_by_node(self, node_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Lấy các quan hệ liên quan tới một node."""
        return self._repository.get_all_node_relationships(node_id=node_id, limit=limit)

    def get_graph_summary(self) -> dict[str, Any]:
        """Thống kê tổng quan dữ liệu hiện có trong đồ thị."""
        nodes_by_type = self._repository.count_nodes_by_type()
        rels_by_type = self._repository.count_relationships_by_type()
        return {
            "nodes": nodes_by_type,
            "relationships": rels_by_type,
            "total_nodes": sum(nodes_by_type.values()),
            "total_relationships": sum(rels_by_type.values()),
        }