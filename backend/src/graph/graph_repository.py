"""
graph_repository.py
Repository layer thực hiện các câu truy vấn Cypher trên Neo4j Knowledge Graph pháp luật Việt Nam.
"""

from typing import Any, Optional

from src.graph.neo4j_client import Neo4jClient
from src.utils.logger import setup_logger

logger = setup_logger(name="graph_repository", filename="graph_repository.log")


class LegalLabels:
    """Các nhãn (Labels) dùng chung trong Knowledge Graph pháp luật."""
    LegalNode = "LegalNode"


class LegalHierarchyLabels:
    """Nhãn biểu diễn các cấp phân cấp văn bản pháp luật theo cấu trúc cây."""
    Document = "Document"       # Văn bản quy phạm pháp luật (Hiến pháp, Bộ luật, Nghị định, Thông tư...)
    Part = "Part"               # Phần (Phần thứ nhất, Phần thứ hai...)
    Chapter = "Chapter"         # Chương (Chương I, Chương II...)
    Section = "Section"         # Mục (Mục 1, Mục 2...)
    SubSection = "SubSection"   # Tiểu mục (Tiểu mục 1, Tiểu mục 2...)
    Article = "Article"         # Điều (Điều 1, Điều 2...)
    Clause = "Clause"           # Khoản (Khoản 1, Khoản 2...)
    Point = "Point"             # Điểm (Điểm a, Điểm b...)


class LegalRelationshipTypes:
    """Các loại quan hệ (Relationship Types) giữa các node trong Knowledge Graph."""
    CONTAINS = "CONTAINS"               # Quan hệ cấu trúc phân cấp cây (Cha CONTAINS Con)
    REFERENCES = "REFERENCES"           # Quan hệ dẫn chiếu / viện dẫn điều khoản khác
    IMPLEMENTS = "IMPLEMENTS"           # Quan hệ hướng dẫn thi hành (Nghị định -> Luật)
    INTERPRETED_BY = "INTERPRETED_BY"   # Quan hệ giải thích, bổ sung quy định
    AMENDS = "AMENDS"                   # Quan hệ sửa đổi, bổ sung quy định
    REPLACES = "REPLACES"               # Quan hệ thay thế quy định
    REPEALS = "REPEALS"                 # Quan hệ bãi bỏ quy định
    RELATED_TO = "RELATED_TO"           # Quan hệ liên quan ngữ nghĩa


class BaseGraphRepository:
    """Lớp cơ sở cung cấp các hàm tiện ích thao tác với Neo4jClient."""

    def __init__(self, db: Neo4jClient):
        self._db = db

    @property
    def db(self) -> Neo4jClient:
        """Truy cập đối tượng Neo4jClient đang quản lý kết nối."""
        return self._db

    def find_all(
        self,
        label: str,
        limit: int = 100,
        order_by: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Lấy danh sách các node theo nhãn (label) kèm giới hạn số lượng và sắp xếp.
        
        Args:
            label: Tên nhãn cần truy vấn (ví dụ 'LegalNode', 'Document', 'Article').
            limit: Số lượng node tối đa cần lấy.
            order_by: Tên thuộc tính dùng để sắp xếp (tùy chọn).
            
        Returns:
            Danh sách dictionary chứa các thuộc tính của các node tìm thấy.
        """
        logger.info(f"Tìm tất cả node có nhãn '{label}', limit={limit}, order_by={order_by}...")

        if order_by:
            query = f"""
            MATCH (n:{label})
            RETURN n, labels(n) AS labels
            ORDER BY n.{order_by} ASC
            LIMIT $limit
            """
        else:
            query = f"""
            MATCH (n:{label})
            RETURN n, labels(n) AS labels
            LIMIT $limit
            """

        rows = self._db.execute_read(query, {"limit": limit})
        logger.info(f"Tìm thấy {len(rows)} node có nhãn '{label}'.")

        return [self._format_node(row) for row in rows]

    @staticmethod
    def _format_node(row: dict[str, Any], node_key: str = "n") -> dict[str, Any]:
        """Chuẩn hóa dữ liệu node từ record truy vấn Neo4j thành dictionary."""
        node_data = dict(row.get(node_key) or {})
        if "labels" in row and row["labels"]:
            node_data["labels"] = row["labels"]
        return node_data


class LegalGraphRepository(BaseGraphRepository):
    """
    Repository chuyên trách các truy vấn Knowledge Graph pháp lý:
    - Tìm kiếm node theo cấp bậc (Document, Chapter, Article, Clause, Point).
    - Phân giải target từ cấu trúc trích dẫn pháp luật.
    - Truy vết đường dẫn tổ tiên (Breadcrumb / Ancestors) và hậu duệ (Descendants / Children).
    - Truy xuất các quan hệ pháp lý (REFERENCES, IMPLEMENTS, INTERPRETED_BY...).
    - Truy vết nguồn gốc tài liệu (Provenance).
    """

    # --------------------------------------------------------------------------
    # 1. TRUY VẤN NODE CƠ BẢN & VĂN BẢN (DOCUMENT)
    # --------------------------------------------------------------------------

    def find_node_by_id(self, node_id: str) -> Optional[dict[str, Any]]:
        """
        Tìm kiếm một node bất kỳ trong đồ thị theo node_id duy nhất.
        
        Args:
            node_id: Mã định danh duy nhất của node (ví dụ: 'HIEN_PHAP_2013_D1', 'BLDS_2015_D27_K1_DIEM_A').
            
        Returns:
            Dict chứa đầy đủ thuộc tính và labels của node, hoặc None nếu không tồn tại.
        """
        logger.info(f"Tìm node theo node_id='{node_id}'...")
        query = """
        MATCH (n:LegalNode {node_id: $node_id})
        RETURN n, labels(n) AS labels
        LIMIT 1
        """
        rows = self._db.execute_read(query, {"node_id": node_id})
        if not rows:
            logger.warning(f"Không tìm thấy node có node_id='{node_id}'.")
            return None
        return self._format_node(rows[0])

    def find_nodes_by_ids(self, node_ids: list[str]) -> list[dict[str, Any]]:
        """
        Lấy thông tin của nhiều node cùng lúc theo danh sách node_ids.
        
        Args:
            node_ids: Danh sách các mã node_id cần truy vấn.
            
        Returns:
            Danh sách các dict chứa dữ liệu node tìm thấy.
        """
        if not node_ids:
            return []
        query = """
        MATCH (n:LegalNode)
        WHERE n.node_id IN $node_ids
        RETURN n, labels(n) AS labels
        """
        rows = self._db.execute_read(query, {"node_ids": node_ids})
        return [self._format_node(row) for row in rows]

    def find_document_by_id(self, document_id: str) -> Optional[dict[str, Any]]:
        """
        Tìm thông tin văn bản quy phạm pháp luật (node :Document) theo document_id.
        
        Args:
            document_id: Mã định danh văn bản (ví dụ: 'HIEN_PHAP_2013', 'BLDS_2015').
            
        Returns:
            Dict chứa metadata của văn bản (số hiệu, ngày hiệu lực, trạng thái...) hoặc None.
        """
        logger.info(f"Tìm văn bản theo document_id='{document_id}'...")
        query = """
        MATCH (d:Document {node_id: $document_id})
        RETURN d, labels(d) AS labels
        LIMIT 1
        """
        rows = self._db.execute_read(query, {"document_id": document_id})
        if not rows:
            logger.warning(f"Không tìm thấy Document có document_id='{document_id}'.")
            return None
        return self._format_node(rows[0], node_key="d")

    def get_all_documents(self) -> list[dict[str, Any]]:
        """
        Lấy danh sách tất cả các văn bản quy phạm pháp luật (:Document) trong đồ thị.
        
        Returns:
            Danh sách các Document node kèm metadata xuất xứ.
        """
        query = """
        MATCH (d:Document)
        RETURN d, labels(d) AS labels
        ORDER BY d.node_id ASC
        """
        rows = self._db.execute_read(query)
        return [self._format_node(row, node_key="d") for row in rows]

    # --------------------------------------------------------------------------
    # 2. TRUY VẤN THEO CẤP BẬC PHÂN CẤP (HIERARCHY RETRIEVAL)
    # --------------------------------------------------------------------------

    def find_chapter(self, document_id: str, chapter_number: str) -> Optional[dict[str, Any]]:
        """
        Tìm node Chương (:Chapter) trong văn bản theo số thứ tự chương (La Mã hoặc số Ả Rập).
        
        Args:
            document_id: Mã định danh văn bản (ví dụ 'HIEN_PHAP_2013').
            chapter_number: Số thứ tự chương (ví dụ 'I', 'IV', '1', '4').
            
        Returns:
            Dict thông tin Chương tìm thấy hoặc None.
        """
        query = """
        MATCH (d:Document {node_id: $document_id})-[:CONTAINS*1..2]->(c:Chapter)
        WHERE toUpper(toString(c.number)) = toUpper($chapter_number)
           OR toString(c.number) = toString($chapter_number)
        RETURN c, labels(c) AS labels
        LIMIT 1
        """
        rows = self._db.execute_read(query, {
            "document_id": document_id,
            "chapter_number": str(chapter_number).strip(),
        })
        if not rows:
            return None
        return self._format_node(rows[0], node_key="c")

    def find_article(
        self,
        document_id: str,
        article_number: int | str,
        chapter_number: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Tìm node Điều (:Article) trong văn bản theo số điều (có thể kèm điều kiện Chương).
        
        Args:
            document_id: Mã định danh văn bản (ví dụ 'BLDS_2015').
            article_number: Số điều (ví dụ 1, 27, 584).
            chapter_number: Số chương (tùy chọn, để thu hẹp phạm vi).
            
        Returns:
            Dict thông tin Điều tìm thấy hoặc None.
        """
        if chapter_number:
            query = """
            MATCH (d:Document {node_id: $document_id})-[:CONTAINS*1..2]->(c:Chapter)
            WHERE toUpper(toString(c.number)) = toUpper($chapter_number)
            MATCH (c)-[:CONTAINS*1..4]->(a:Article)
            WHERE toString(a.number) = toString($article_number)
            RETURN a, labels(a) AS labels
            LIMIT 1
            """
            params = {
                "document_id": document_id,
                "chapter_number": str(chapter_number).strip(),
                "article_number": str(article_number).strip(),
            }
        else:
            query = """
            MATCH (d:Document {node_id: $document_id})-[:CONTAINS*1..6]->(a:Article)
            WHERE toString(a.number) = toString($article_number)
            RETURN a, labels(a) AS labels
            LIMIT 1
            """
            params = {
                "document_id": document_id,
                "article_number": str(article_number).strip(),
            }

        rows = self._db.execute_read(query, params)
        if not rows:
            return None
        return self._format_node(rows[0], node_key="a")

    def find_clause(
        self,
        article_node_id: str,
        clause_number: int | str,
    ) -> Optional[dict[str, Any]]:
        """
        Tìm node Khoản (:Clause) thuộc một Điều theo số thứ tự khoản.
        
        Args:
            article_node_id: Mã node_id của Điều cha (ví dụ 'BLDS_2015_D27').
            clause_number: Số thứ tự khoản (ví dụ 1, 2).
            
        Returns:
            Dict thông tin Khoản hoặc None.
        """
        query = """
        MATCH (a:Article {node_id: $article_node_id})-[:CONTAINS]->(k:Clause)
        WHERE toString(k.number) = toString($clause_number)
        RETURN k, labels(k) AS labels
        LIMIT 1
        """
        rows = self._db.execute_read(query, {
            "article_node_id": article_node_id,
            "clause_number": str(clause_number).strip(),
        })
        if not rows:
            return None
        return self._format_node(rows[0], node_key="k")

    def find_point(
        self,
        clause_node_id: str,
        point_letter: str,
    ) -> Optional[dict[str, Any]]:
        """
        Tìm node Điểm (:Point) thuộc một Khoản theo ký tự chữ cái (ví dụ 'a', 'b', 'c').
        
        Args:
            clause_node_id: Mã node_id của Khoản cha (ví dụ 'BLDS_2015_D27_K1').
            point_letter: Chữ cái điểm (ví dụ 'a', 'b').
            
        Returns:
            Dict thông tin Điểm hoặc None.
        """
        query = """
        MATCH (k:Clause {node_id: $clause_node_id})-[:CONTAINS]->(p:Point)
        WHERE toLower(toString(p.number)) = toLower($point_letter)
        RETURN p, labels(p) AS labels
        LIMIT 1
        """
        rows = self._db.execute_read(query, {
            "clause_node_id": clause_node_id,
            "point_letter": str(point_letter).strip(),
        })
        if not rows:
            return None
        return self._format_node(rows[0], node_key="p")

    def find_node_by_hierarchy(
        self,
        document_id: str,
        part: Optional[str] = None,
        chapter: Optional[str] = None,
        section: Optional[str] = None,
        subsection: Optional[str] = None,
        article: Optional[int | str] = None,
        clause: Optional[int | str] = None,
        point: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Truy vấn tìm kiếm node sâu nhất khớp với cấu trúc trích dẫn mục tiêu (Target)
        trong cây phân cấp (:CONTAINS) của một văn bản pháp luật.
        
        Thứ tự giải quyết từ chi tiết nhất đến tổng quát nhất:
        Point -> Clause -> Article -> SubSection -> Section -> Chapter -> Part -> Document.
        
        Args:
            document_id: Mã văn bản (ví dụ 'BLDS_2015').
            part: Phần (nếu có).
            chapter: Chương (nếu có).
            section: Mục (nếu có).
            subsection: Tiểu mục (nếu có).
            article: Điều (nếu có).
            clause: Khoản (nếu có).
            point: Điểm (nếu có).
            
        Returns:
            Dict thông tin node sâu nhất khớp với yêu cầu hoặc None.
        """
        logger.info(
            f"Phân giải node phân cấp: doc={document_id}, art={article}, "
            f"k={clause}, diem={point}, ch={chapter}, sec={section}"
        )

        # 1. Có Điều: tìm Article trước, sau đó đào sâu xuống Clause và Point
        if article is not None:
            article_node = self.find_article(
                document_id=document_id,
                article_number=article,
                chapter_number=chapter,
            )
            if not article_node:
                logger.warning(f"Không tìm thấy Điều {article} trong văn bản '{document_id}'.")
                return None

            # Nếu có Khoản:
            if clause is not None:
                clause_node = self.find_clause(
                    article_node_id=article_node["node_id"],
                    clause_number=clause,
                )
                if not clause_node:
                    logger.warning(
                        f"Không tìm thấy Khoản {clause} trong Điều '{article_node['node_id']}'."
                    )
                    return None

                # Nếu có Điểm:
                if point is not None:
                    point_node = self.find_point(
                        clause_node_id=clause_node["node_id"],
                        point_letter=point,
                    )
                    if not point_node:
                        logger.warning(
                            f"Không tìm thấy Điểm {point} trong Khoản '{clause_node['node_id']}'."
                        )
                        return None
                    return point_node

                return clause_node

            return article_node

        # 2. Không có Điều, tìm theo Chương
        if chapter is not None:
            chapter_node = self.find_chapter(document_id=document_id, chapter_number=chapter)
            if chapter_node:
                return chapter_node

        # 3. Tìm theo Phần
        if part is not None:
            query = """
            MATCH (d:Document {node_id: $document_id})-[:CONTAINS]->(p:Part)
            WHERE toLower(toString(p.number)) = toLower($part)
               OR toString(p.number) = toString($part)
            RETURN p, labels(p) AS labels
            LIMIT 1
            """
            rows = self._db.execute_read(query, {"document_id": document_id, "part": str(part).strip()})
            if rows:
                return self._format_node(rows[0], node_key="p")

        # 4. Fallback về Document
        return self.find_document_by_id(document_id)

    # --------------------------------------------------------------------------
    # 3. TRUY VẤN PHẢ HỆ & CÂY CON (ANCESTORS / BREADCRUMB / DESCENDANTS)
    # --------------------------------------------------------------------------

    def get_ancestors(self, node_id: str) -> list[dict[str, Any]]:
        """
        Truy vết chuỗi tổ tiên (Breadcrumb) từ gốc Document tới node hiện tại theo quan hệ CONTAINS.
        
        Ví dụ thứ tự kết quả: Document -> Part -> Chapter -> Section -> Article -> Clause -> Point.
        
        Args:
            node_id: Mã định danh node cần lấy phả hệ.
            
        Returns:
            Danh sách các dict tóm tắt thông tin từng node trên đường dẫn:
            [{node_id, type, number, title, parent_id, document_id, labels}, ...]
        """
        query = """
        MATCH path = (doc:Document)-[:CONTAINS*0..7]->(n:LegalNode {node_id: $node_id})
        RETURN [x IN nodes(path) | {
            node_id: x.node_id,
            type: [l IN labels(x) WHERE l <> 'LegalNode'][0],
            number: x.number,
            title: x.title,
            parent_id: x.parent_id,
            document_id: x.document_id,
            labels: labels(x)
        }] AS breadcrumb
        LIMIT 1
        """
        rows = self._db.execute_read(query, {"node_id": node_id})
        if not rows or not rows[0].get("breadcrumb"):
            return []
        return rows[0]["breadcrumb"]

    def get_children(self, node_id: str) -> list[dict[str, Any]]:
        """
        Lấy danh sách các node con trực tiếp nối bởi quan hệ (n)-[:CONTAINS]->(child).
        
        Args:
            node_id: Mã định danh node cha.
            
        Returns:
            Danh sách node con được sắp xếp theo thứ tự số hiệu (number).
        """
        query = """
        MATCH (n:LegalNode {node_id: $node_id})-[:CONTAINS]->(c:LegalNode)
        RETURN c, labels(c) AS labels
        ORDER BY c.number ASC
        """
        rows = self._db.execute_read(query, {"node_id": node_id})
        return [self._format_node(row, node_key="c") for row in rows]

    def get_descendants(
        self,
        node_id: str,
        max_depth: int = 5,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """
        Lấy toàn bộ cây node con cháu bên dưới theo quan hệ CONTAINS đến độ sâu max_depth.
        (Ví dụ lấy toàn bộ Điều trong một Chương, hoặc toàn bộ Khoản và Điểm trong một Điều).
        
        Args:
            node_id: Mã node gốc cần lấy con cháu.
            max_depth: Độ sâu tối đa duyệt cây (mặc định 5).
            limit: Giới hạn số lượng node trả về.
            
        Returns:
            Danh sách các node con cháu kèm thông tin độ sâu (depth).
        """
        query = """
        MATCH path = (n:LegalNode {node_id: $node_id})-[:CONTAINS*1..5]->(d:LegalNode)
        WHERE length(path) <= $max_depth
        RETURN d, labels(d) AS labels, length(path) AS depth
        ORDER BY depth ASC, d.number ASC
        LIMIT $limit
        """
        rows = self._db.execute_read(query, {"node_id": node_id, "max_depth": max_depth, "limit": limit})
        results = []
        for row in rows:
            node = self._format_node(row, node_key="d")
            node["depth"] = row.get("depth", 1)
            results.append(node)
        return results

    # --------------------------------------------------------------------------
    # 4. TRUY VẤN QUAN HỆ PHÁP LÝ & DẪN CHIẾU (RELATIONSHIPS & REFERENCES)
    # --------------------------------------------------------------------------

    def get_outgoing_relationships(
        self,
        node_id: str,
        relation_types: Optional[list[str]] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Lấy các quan hệ đi ra từ node này tới các node khác: (n)-[r]->(target).
        Ví dụ dẫn chiếu tới quy định khác: REFERENCES, IMPLEMENTS, AMENDS, RELATED_TO.
        
        Args:
            node_id: Mã node nguồn.
            relation_types: Danh sách các loại quan hệ cần lọc (mặc định lấy tất cả trừ CONTAINS).
            limit: Số lượng tối đa.
            
        Returns:
            Danh sách các dict chứa thông tin quan hệ, thuộc tính cạnh (evidence, confidence) và node đích.
        """
        query = """
        MATCH (n:LegalNode {node_id: $node_id})-[r]->(m:LegalNode)
        WHERE ($rel_types IS NULL AND type(r) <> 'CONTAINS') OR type(r) IN $rel_types
        RETURN
            type(r) AS relation_type,
            properties(r) AS properties,
            m AS target_node,
            labels(m) AS target_labels
        LIMIT $limit
        """
        rows = self._db.execute_read(query, {
            "node_id": node_id,
            "rel_types": relation_types,
            "limit": limit,
        })
        results = []
        for row in rows:
            target = dict(row.get("target_node") or {})
            target["labels"] = row.get("target_labels", [])
            results.append({
                "relation_type": row["relation_type"],
                "properties": dict(row.get("properties") or {}),
                "target_node": target,
                "direction": "OUTGOING",
            })
        return results

    def get_incoming_relationships(
        self,
        node_id: str,
        relation_types: Optional[list[str]] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Lấy các quan hệ đi vào node này từ các node khác: (source)-[r]->(n).
        Ví dụ được văn bản khác hướng dẫn hay dẫn chiếu: INTERPRETED_BY, REPLACED_BY, REFERENCES.
        
        Args:
            node_id: Mã node đích.
            relation_types: Danh sách loại quan hệ cần lọc (mặc định lấy tất cả trừ CONTAINS).
            limit: Số lượng tối đa.
            
        Returns:
            Danh sách các dict chứa quan hệ và node nguồn.
        """
        query = """
        MATCH (m:LegalNode)-[r]->(n:LegalNode {node_id: $node_id})
        WHERE ($rel_types IS NULL AND type(r) <> 'CONTAINS') OR type(r) IN $rel_types
        RETURN
            type(r) AS relation_type,
            properties(r) AS properties,
            m AS source_node,
            labels(m) AS source_labels
        LIMIT $limit
        """
        rows = self._db.execute_read(query, {
            "node_id": node_id,
            "rel_types": relation_types,
            "limit": limit,
        })
        results = []
        for row in rows:
            source = dict(row.get("source_node") or {})
            source["labels"] = row.get("source_labels", [])
            results.append({
                "relation_type": row["relation_type"],
                "properties": dict(row.get("properties") or {}),
                "source_node": source,
                "direction": "INCOMING",
            })
        return results

    def get_all_node_relationships(
        self,
        node_id: str,
        relation_types: Optional[list[str]] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Lấy cả quan hệ đi ra (outgoing) và đi vào (incoming) của một node.
        
        Args:
            node_id: Mã định danh node.
            relation_types: Danh sách loại quan hệ cần lọc (mặc định loại trừ CONTAINS).
            limit: Số lượng tối đa.
            
        Returns:
            Danh sách tất cả các mối quan hệ kèm trường direction ('OUTGOING' hoặc 'INCOMING').
        """
        half_limit = max(1, limit // 2)
        outgoing = self.get_outgoing_relationships(node_id, relation_types, limit=half_limit)
        incoming = self.get_incoming_relationships(node_id, relation_types, limit=half_limit)
        return outgoing + incoming

    def get_related_legal_nodes(
        self,
        node_id: str,
        hops: int = 1,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Truy xuất các node pháp luật liên quan trong phạm vi 1 hoặc 2 hop (bỏ qua quan hệ CONTAINS),
        giúp mở rộng mạng lưới viện dẫn pháp luật cho AI suy luận.
        
        Args:
            node_id: Node gốc.
            hops: Số bước nhảy (1 hoặc 2).
            limit: Số lượng node tối đa.
            
        Returns:
            Danh sách các node liên quan kèm thông tin chuỗi quan hệ và khoảng cách hop.
        """
        if hops <= 1:
            query = """
            MATCH (n:LegalNode {node_id: $node_id})-[r]-(m:LegalNode)
            WHERE type(r) <> 'CONTAINS' AND n.node_id <> m.node_id
            RETURN DISTINCT
                m AS related_node,
                labels(m) AS labels,
                type(r) AS relation_type,
                properties(r) AS properties,
                1 AS hop_distance
            LIMIT $limit
            """
            rows = self._db.execute_read(query, {"node_id": node_id, "limit": limit})
            results = []
            for row in rows:
                node = dict(row.get("related_node") or {})
                node["labels"] = row.get("labels", [])
                results.append({
                    "related_node": node,
                    "relation_type": row.get("relation_type"),
                    "properties": dict(row.get("properties") or {}),
                    "hop_distance": 1,
                })
            return results

        # 2 hops
        query = """
        MATCH path = (n:LegalNode {node_id: $node_id})-[r*1..2]-(m:LegalNode)
        WHERE ALL(rel IN relationships(path) WHERE type(rel) <> 'CONTAINS')
          AND n.node_id <> m.node_id
        RETURN DISTINCT
            m AS related_node,
            labels(m) AS labels,
            length(path) AS hop_distance,
            [rel IN relationships(path) | type(rel)] AS relation_chain,
            [rel IN relationships(path) | properties(rel)] AS relation_properties
        LIMIT $limit
        """
        rows = self._db.execute_read(query, {"node_id": node_id, "limit": limit})
        results = []
        for row in rows:
            node = dict(row.get("related_node") or {})
            node["labels"] = row.get("labels", [])
            results.append({
                "related_node": node,
                "hop_distance": row.get("hop_distance", 2),
                "relation_chain": row.get("relation_chain", []),
                "relation_properties": row.get("relation_properties", []),
            })
        return results

    # --------------------------------------------------------------------------
    # 5. TRUY VẾT NGUỒN GỐC & HIỆU LỰC (PROVENANCE & VERIFICATION)
    # --------------------------------------------------------------------------

    def get_document_provenance(self, document_id: str) -> Optional[dict[str, Any]]:
        """
        Lấy thông tin nguồn gốc, số hiệu, ngày ban hành, hiệu lực và link văn bản gốc
        từ node :Document để phục vụ kiểm chứng chống bịa đặt (Anti-hallucination).
        
        Args:
            document_id: Mã văn bản (ví dụ 'HIEN_PHAP_2013', 'BLDS_2015').
            
        Returns:
            Dict chứa thông tin xuất xứ đầy đủ hoặc None.
        """
        query = """
        MATCH (d:Document {node_id: $document_id})
        RETURN {
            document_id: d.node_id,
            title: d.title,
            so_hieu: d.number,
            issuer: d.issuer,
            effective_from: d.effective_from,
            status: d.status,
            source_file: d.source_file,
            source_url: d.source_url,
            metadata_source: d.metadata_source,
            verified_at: d.verified_at
        } AS provenance
        LIMIT 1
        """
            # effective_to: d.effective_to, Chưa có
        rows = self._db.execute_read(query, {"document_id": document_id})
        if not rows or not rows[0].get("provenance"):
            return None
        return rows[0]["provenance"]

    def get_node_provenance(self, node_id: str) -> Optional[dict[str, Any]]:
        """
        Lấy thông tin xuất xứ văn bản của một node bất kỳ (truy ngược về Document cha).
        
        Args:
            node_id: Mã định danh node bất kỳ.
            
        Returns:
            Dict chứa provenance của văn bản chứa node đó.
        """
        query = """
        MATCH (n:LegalNode {node_id: $node_id})
        MATCH (d:Document {node_id: n.document_id})
        RETURN {
            document_id: d.node_id,
            title: d.title,
            so_hieu: d.number,
            issuer: d.issuer,
            effective_from: d.effective_from,
            effective_to: d.effective_to,
            status: d.status,
            source_file: d.source_file,
            source_url: d.source_url,
            metadata_source: d.metadata_source,
            verified_at: d.verified_at
        } AS provenance
        LIMIT 1
        """
        rows = self._db.execute_read(query, {"node_id": node_id})
        if not rows or not rows[0].get("provenance"):
            return None
        return rows[0]["provenance"]

    # --------------------------------------------------------------------------
    # 6. THỐNG KÊ & QUẢN TRỊ ĐỒ THỊ (STATISTICS & AUDIT)
    # --------------------------------------------------------------------------

    def count_nodes_by_type(self) -> dict[str, int]:
        """
        Thống kê số lượng node theo từng loại cấu trúc (Document, Chapter, Article...).
        
        Returns:
            Dict dạng {type_name: count}.
        """
        query = """
        MATCH (n:LegalNode)
        RETURN n.type AS node_type, count(n) AS total
        ORDER BY total DESC
        """
        rows = self._db.execute_read(query)
        return {row["node_type"]: row["total"] for row in rows if row.get("node_type")}

    def count_relationships_by_type(self) -> dict[str, int]:
        """
        Thống kê số lượng quan hệ theo từng loại (CONTAINS, REFERENCES, IMPLEMENTS...).
        
        Returns:
            Dict dạng {rel_type: count}.
        """
        query = """
        MATCH ()-[r]->()
        RETURN type(r) AS rel_type, count(r) AS total
        ORDER BY total DESC
        """
        rows = self._db.execute_read(query)
        return {row["rel_type"]: row["total"] for row in rows if row.get("rel_type")}

    def get_all_relationships(
        self,
        label: str = "LegalNode",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Lấy danh sách tất cả các mối quan hệ giữa các node trong đồ thị.
        
        Args:
            label: Nhãn node cần xét (mặc định 'LegalNode').
            limit: Giới hạn số lượng trả về.
            
        Returns:
            Danh sách các dict chứa source_id, relation_type, target_id và properties.
        """
        query = f"""
        MATCH (s:{label})-[r]->(t:{label})
        RETURN
            s.node_id AS source_id,
            type(r) AS relation_type,
            t.node_id AS target_id,
            properties(r) AS properties
        ORDER BY source_id, relation_type, target_id
        LIMIT $limit
        """
        rows = self._db.execute_read(query, {"limit": limit})
        return [
            {
                "source_id": row["source_id"],
                "relation_type": row["relation_type"],
                "target_id": row["target_id"],
                "properties": dict(row.get("properties") or {}),
            }
            for row in rows
        ]