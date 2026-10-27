import json
from typing import Any, Optional

from src.common.constants import LegalHierarchyLabels, MinimumScoreThresholds
from src.common.custom_exception import CustomException
from src.common.schemas import LegalHierarchy
from src.graph.graph_service import LegalGraphService
from src.models.legal_model import BaseLegalModel
from src.retrieval.legal_query_extractor import LegalQueryExtractor
from src.retrieval.semantic import SemanticSearcher
from src.retrieval.hybrid import HybridSearcher
from src.utils.logger import setup_logger

logger = setup_logger("retrieval_service", filename="retrieval_service.log")

#  Duyệt đồ thị neuro symbolic theo các yêu cầu từ retrieval service
#  Được sử dụng trực tiếp với retrieval service


from src.graph.graph_service import LegalGraphService


class GraphTraverse:
    def __init__(self, graph_service: LegalGraphService):
        self._legal_graph_service = graph_service

    # Duyệt các nốt hậu duệ của node hiện tại

    # Lọc các document trong danh sách các nodes truyền vào chứa document_id

    # Tìm kiếm các quan hệ pháp lý của một nốt với các node khác ngoại trừ CONTAINS

    # Duyệt các quan hệ của danh sach các nodes

    def collect_related_nodes(self, seed_ids: list[str]) -> list[dict[str, Any]]:
        """Gom node đích/seed + cha + con + con cháu, khử trùng theo node_id.

        Node `Document` bị loại khỏi `related_nodes` vì đã phản ánh trong `related_documents`.

        Args:
            seed_ids: Danh sách node_id gốc đã chạm được.

        Returns:
            Danh sách node theo thứ tự: seed trước, rồi cha, con, con cháu.
        """
        collected: dict[str, dict[str, Any]] = {}

        def add(node: Optional[dict[str, Any]]) -> None:
            """Thêm node vào tập kết quả nếu hợp lệ và chưa có."""
            if not node:
                return
            node_id = node.get("node_id")
            if not node_id or node_id in collected:
                return
            if node.get("label") == "Document":
                return
            collected[node_id] = node

        for seed_id in seed_ids:
            if not seed_id:
                continue
            add(self._legal_graph_service.get_node_by_id(seed_id))
            for ancestor in self._legal_graph_service.get_breadcrumbs(seed_id):
                add(ancestor)
            for child in self._legal_graph_service.get_children(seed_id):
                add(child)
            for descendant in self._legal_graph_service.get_descendants(
                seed_id, max_depth=5, limit=200
            ):
                add(descendant)

        return list(collected.values())

    def collect_legal_relationships(
        self, seed_ids: list[str]
    ) -> list[tuple[str, dict[str, Any]]]:
        """Lấy quan hệ pháp lý của từng seed, gắn kèm node gốc để định hướng cạnh.

        Args:
            seed_ids: Danh sách node_id gốc.

        Returns:
            Danh sách cặp (node_id gốc, bản ghi quan hệ).
        """
        relationships: list[tuple[str, dict[str, Any]]] = []
        for seed_id in seed_ids:
            if not seed_id:
                continue
            for relationship in self._legal_graph_service.get_related_laws(
                seed_id, limit=50
            ):
                relationships.append((seed_id, relationship))
        return relationships

    def collect_related_documents(
        self,
        document_ids: list[str],
        nodes: list[dict[str, Any]],
        legal_relationships: list[tuple[str, dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """Gom provenance các văn bản liên quan (văn bản resolve + văn bản của node/quan hệ).

        Args:
            document_ids: Document_id khởi điểm (văn bản resolve được).
            nodes: Các node đã gom.
            legal_relationships: Các quan hệ pháp lý đã gom.

        Returns:
            Danh sách provenance đã chuẩn hoá, khử trùng theo document_id.
        """
        collected: dict[str, dict[str, Any]] = {}

        def add_document(document_id: Optional[str]) -> None:
            """Thêm provenance của một văn bản nếu chưa có."""
            if not document_id or document_id in collected:
                return
            provenance = self._legal_graph_service.get_document_provenance(document_id)
            if provenance:
                collected[document_id] = provenance

        for document_id in document_ids:
            add_document(document_id)
        for node in nodes:
            add_document(node.get("document_id"))
        for _, relationship in legal_relationships:
            for key in ("target_node", "source_node", "related_node"):
                related_node = relationship.get(key)
                if related_node:
                    add_document(related_node.get("document_id"))

        return list(collected.values())

    def build_relationships(
        self,
        nodes: list[dict[str, Any]],
        legal_relationships: list[tuple[str, dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """Gộp quan hệ cấu trúc (CONTAINS) và quan hệ pháp lý thành mảng phẳng.

        Args:
            nodes: Các node đã gom (dùng `parent_id` để suy cạnh CONTAINS).
            legal_relationships: Các cặp (node gốc, bản ghi quan hệ pháp lý).

        Returns:
            Danh sách quan hệ {from_node_id, to_node_id, relationship_type}, khử trùng lặp.
        """
        collected: dict[tuple[str, str, str], dict[str, Any]] = {}

        def add(
            from_node_id: Optional[str],
            to_node_id: Optional[str],
            relationship_type: Optional[str],
        ) -> None:
            """Thêm một cạnh nếu đủ thông tin và chưa tồn tại."""
            if not from_node_id or not to_node_id or not relationship_type:
                return
            key = (from_node_id, relationship_type, to_node_id)
            if key in collected:
                return
            collected[key] = {
                "from_node_id": from_node_id,
                "to_node_id": to_node_id,
                "relationship_type": relationship_type,
            }

        # Cạnh cấu trúc CONTAINS suy từ parent_id của các node đã gom.
        for node in nodes:
            add(node.get("parent_id"), node.get("node_id"), "CONTAINS")

        # Cạnh quan hệ pháp lý (REFERENCES, IMPLEMENTS, INTERPRETED_BY...).
        for root_id, relationship in legal_relationships:
            relationship_type = relationship.get("relation_type")
            if relationship.get("direction") == "INCOMING":
                source = relationship.get("source_node") or {}
                add(source.get("node_id"), root_id, relationship_type)
            else:
                target = relationship.get("target_node") or {}
                add(root_id, target.get("node_id"), relationship_type)

        return list(collected.values())


class RetrievalService:
    """Điều phối pipeline Retrieval V1 và dựng output 6 key theo đặc tả."""

    def __init__(
        self,
        legal_query_extractor: LegalQueryExtractor,
        legal_graph_service: LegalGraphService,
        semantic_service: SemanticSearcher,
        hybrid_service: Optional[HybridSearcher] = None,
    ):
        """Khởi tạo orchestrator.

        Args:
            legal_graph_service: Service truy vấn đồ thị.
            legal_query_extractor: Bộ parse câu hỏi -> phân cấp.
            semantic_service: Service tìm kiếm ngữ nghĩa.
            hybrid_service: Service tìm kiếm kết hợp Hybrid (Semantic + BM25).
        """
        self._semantic_service = semantic_service
        self._legal_graph_service = legal_graph_service
        self._extractor = legal_query_extractor
        self._hybrid_service = hybrid_service

    def format_node(self, node: dict[str, Any]) -> dict[str, Any]:
        """Giữ nguyên toàn bộ field gốc của node và bổ sung `citation` tuyệt đối.

        Args:
            node: Dict node đọc từ graph.

        Returns:
            Dict gồm toàn bộ field gốc của node + `citation`.
        """
        node_id = node.get("node_id")
        return {
            **node,
            "citation": self._legal_graph_service.get_citation_path(node_id),
        }

    def retrieve(
        self,
        query_text: str,
    ) -> dict[str, Any]:
        """Chạy pipeline Retrieval V1 cho một câu hỏi.

        Args:
            query_text: Câu hỏi người dùng (có trích dẫn vị trí luật).

        Returns:
            {
                "input": query_text,
                "extracted_hierarchy": dict,  # phân cấp parse được từ câu hỏi
                "node_information": dict,  # thông tin node parse được từ câu hỏi
                "related_documents": list[dict],  # danh sách document liên quan
                "related_nodes": list[dict],  # danh sách node liên quan
                "relationships": list[dict],  # danh sách quan hệ giữa các node liên quan
            }
        """

        logger.info(f"Nhận câu hỏi: {query_text}")

        # Khử trùng theo id (dict giữ thứ tự chèn, tránh lỗi set không chứa được dict).
        related_documents: dict[str, dict[str, Any]] = {}
        related_nodes: dict[str, dict[str, Any]] = {}
        related_relationships: list[tuple[str, dict[str, Any]]] = []

        # # văn bản hard code để test (vì chưa có model trích xuất document_name từ câu hỏi)
        # default_document = "Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013"

        # # (1) Parse cấu trúc từ câu hỏi.
        # extracted = self._extractor.extract_hierarchy(
        #     query_text=query_text, document=default_document
        # )

        # Dùng khi có model tự trích xuất
        extracted = self._extractor.extract_hierarchy_with_model(query_text=query_text)

        has_hierarchy = extracted.get("has_hierarchy", False)
        valid_hierarchy = extracted.get("valid_hierarchy", False)
        hierarchy_dict = extracted.get("hierarchy", {})
        hierarchy = LegalHierarchy.from_dict(hierarchy_dict)

        logger.info("Kiểm tra hợp lệ phân cấp: " + str(valid_hierarchy))
        logger.info(
            f"Phân cấp parse được từ câu hỏi: {json.dumps(hierarchy_dict, ensure_ascii=False)}"
        )

        EMPTY_RESULT = {
            "input": query_text,
            "extracted_hierarchy": hierarchy_dict,
            "node_information": None,
            "related_documents": [],
            "related_nodes": [],
            "relationships": [],
        }

        is_document_type = False
        if has_hierarchy:
            try:
                node_type = hierarchy.get_node_type()
                is_document_type = node_type == LegalHierarchyLabels.Document
            except CustomException:
                has_hierarchy = False

            if has_hierarchy and hierarchy.document:
                # Lọc semantic kiểm trả document có chính xác hay tồn tại trong graph, nếu score thấp sẽ bỏ qua
                semantic_search_documents = (
                    self._semantic_service.semantic_search_by_text_and_label(
                        text=hierarchy.document,
                        label=LegalHierarchyLabels.Document,
                        top_k=1,
                    )
                )

                if (
                    not semantic_search_documents
                    or semantic_search_documents[0].get("score", 0)
                    < MinimumScoreThresholds.SEMANTIC_SEARCH_DOCUMENTS
                ):
                    logger.warning(
                        f"Không tìm thấy document chính xác từ semantic search cho document: {hierarchy.document}"
                    )
                    hierarchy.document = None
                    has_hierarchy = False

        # Nếu có cấu trúc phân cấp thì search theo phân cấp,
        if has_hierarchy and not is_document_type:
            logger.info(f"Tìm kiếm thông tin node theo phân cấp đã trích xuất")
            # Phân cấp không hợp lệ thì return và lỗi
            if not valid_hierarchy:
                raise CustomException(
                    f"Phân cấp parse được từ câu hỏi không hợp lệ: {json.dumps(hierarchy_dict, ensure_ascii=False)}",
                    status_code=400,
                )

            # Tìm kiếm theo document name với semantic để lấy top document liên quan
            logger.info(
                f"Tìm kiếm ngữ nghĩa (semantic search) theo document name: {hierarchy.document}"
            )
            semantic_search_documents = (
                self._semantic_service.semantic_search_by_text_and_label(
                    text=hierarchy.document,
                    label=LegalHierarchyLabels.Document,
                    top_k=5,
                )
            )
            logger.info(
                f"Kết quả tìm kiếm ngữ nghĩa: {len(semantic_search_documents)} results."
            )

            # Duyệt các doc vừa tìm để tạo node
            for doc in semantic_search_documents:
                label = doc.get("label")
                # Nếu khong phải document thì bỏ qua
                if label != LegalHierarchyLabels.Document:
                    logger.warning(
                        f"Document {doc.get('title')} (document_id: {doc.get('document_id')}) bị loại bỏ do label không phải Document ({label})."
                    )
                    continue

                document_id = doc.get("document_id") or doc.get("node_id")
                document_name = doc.get("title")
                score = doc.get("score", 0)

                logger.info(
                    f"Kiểm tra document: {document_name} (document_id: {document_id}) (score: {score})"
                )

                if document_id is None:
                    continue

                # Lọc document theo score threshold
                if score < MinimumScoreThresholds.SEMANTIC_SEARCH_DOCUMENTS:
                    logger.warning(
                        f"Document {document_name} (document_id: {document_id}) bị loại bỏ do score thấp ({score} < {MinimumScoreThresholds.SEMANTIC_SEARCH_DOCUMENTS})."
                    )
                    continue

                # Thử nghiệm tạo node_id từ document_id, nếu không có thì bỏ qua
                node_id = hierarchy.get_node_id_from_document_id(
                    document_id=document_id
                )
                if node_id is None:
                    logger.warning(
                        f"Không thể tạo node_id từ document_id: {document_id}"
                    )
                    continue

                # tìm kiếm node trên graph
                # Không có thì loại bỏ,
                node = self._legal_graph_service.get_node_by_id(node_id)
                if node is None:
                    logger.warning(f"Không tìm thấy node với node_id {node_id}")
                    continue

                logger.info(f"Tìm thấy node với node_id {node_id}")

                # tìm các node con, cháu và thêm vào tập kết quả (khử trùng theo node_id)
                related_nodes[node_id] = node
                seed_ids = [node_id]

                # gom các node liên quan (cha, con, con cháu) và quan hệ pháp lý
                logger.info(
                    f"Gom các node liên quan (cha, con, con cháu) và quan hệ pháp lý"
                )
                nodes = self._collect_related_nodes(seed_ids)
                for n in nodes:
                    related_nodes[n["node_id"]] = n

                # related relationships
                logger.info(f"Gom các quan hệ pháp lý của các node liên quan")
                legal_relationships = self._collect_legal_relationships(seed_ids)
                related_relationships.extend(legal_relationships)

                logger.info(f"Quan hệ pháp lý liên quan: {legal_relationships}.")

                related_documents[document_id] = doc

            # Nếu không có node và document nào được tìm thấy, return
            if (not related_nodes or len(related_nodes) == 0) and (
                not related_documents or len(related_documents) == 0
            ):
                logger.warning(
                    "Không tìm thấy node hoặc document nào liên quan từ phân cấp parse được."
                )
                return EMPTY_RESULT

            # =======================================================
            # lọc lại các node liên quan nhất với query_text bằng semantic search, giảm số lượng node cần xử lý bước sau
            # RERANKING: kiểm trả các node liên quan có khớp nội dung không
            # trả về các node liên quan, các document chứa node liên quan, các quan hệ pháp lý
            # =======================================================

            # Chọn lọc Document chính xác nhất là document  của node, không loại doc liên quan
            # Kiểm tra chính tả vì có thể sai tên document và semantic không chính xác hoàn toàn
            logger.info(
                f"Lọc document chính xác nhất của node, không loại doc liên quan"
            )
            top_score = 0
            for doc in semantic_search_documents:
                score = doc.get("score", 0)
                if score > top_score:
                    top_score = score
                    hierarchy.document = doc.get("title")
                    hierarchy_dict = hierarchy.to_dict()
            logger.info(
                f"Document chính xác nhất của node: {hierarchy.document} (score: {top_score})"
            )

            logger.info(
                f"Tổng hợp kết quả: {len(related_nodes)} nodes, {len(related_documents)} documents, {len(related_relationships)} relationships."
            )

            return {
                "input": query_text,
                "extracted_hierarchy": hierarchy_dict,
                "node_information": hierarchy.get_all_info() if hierarchy else None,
                "related_documents": [
                    self.format_node(doc) for doc in related_documents.values()
                ],
                "related_nodes": [
                    self.format_node(node) for node in related_nodes.values()
                ],
                "relationships": self._build_relationships(
                    nodes=list(related_nodes.values()),
                    legal_relationships=related_relationships,
                ),
            }

        # Nếu không có phân cấp: hybrid search (V2) hoặc semantic search (V1) để tìm node liên quan.
        if not has_hierarchy or is_document_type:
            logger.info(
                f"Không tìm thấy phân cấp trong câu hỏi, sẽ tìm kiếm node liên quan bằng Hybrid/Semantic search."
            )

            # Ưu tiên Hybrid Search nếu được inject, ngược lại dùng Semantic Search
            searcher = (
                self._hybrid_service
                if self._hybrid_service is not None
                else self._semantic_service
            )
            search_nodes = searcher.search(
                query=query_text,
                top_k=10,
            )

            if not search_nodes or "results" not in search_nodes:
                logger.warning(
                    "Không tìm thấy node hoặc document nào liên quan từ search service."
                )
                return EMPTY_RESULT

            related_nodes_found = search_nodes.get("related_nodes", [])
            related_documents_found = search_nodes.get(
                "related_documents", []
            )

            logger.info(
                f"Kết quả tìm kiếm liên quan: {len(related_nodes_found)} nodes, {len(related_documents_found)} documents."
            )

            if not related_nodes_found and not related_documents_found:
                logger.warning(
                    "Không tìm thấy node hoặc document nào liên quan từ search service."
                )
                return EMPTY_RESULT

            # Gom trước các document đã tìm thấy từ tầng search
            for doc in related_documents_found:
                did = doc.get("node_id") or doc.get("document_id")
                if did and did not in related_documents:
                    related_documents[did] = doc

            # Duyệt kết quả tìm kiếm làm Seed Nodes để mở rộng đồ thị
            for node in related_nodes_found:
                node_id = node.get("node_id")
                if not node_id:
                    logger.error(f"Node không có node_id, bỏ qua: {node}")
                    continue

                # check score threshold
                score = node.get("score", 0)
                is_hybrid = (
                    node.get("retrieval_source", "").startswith("hybrid")
                    or "rrf_score" in node
                )
                node_text = (
                    node.get("title")
                    or node.get("text")
                    or node.get("full_text")
                    or "Unknown"
                )

                if is_hybrid:
                    # Với Hybrid RRF, loại bỏ các kết quả có score <= 0
                    if score <= 0:
                        continue
                else:
                    # Với Semantic Cosine thuần, lọc theo ngưỡng tối thiểu
                    if score < MinimumScoreThresholds.SEMANTIC_SEARCH_NODES:
                        logger.warning(
                            f"Node {node_text} (node_id: {node_id}) bị loại bỏ do score thấp ({score} < {MinimumScoreThresholds.SEMANTIC_SEARCH_NODES})."
                        )
                        continue

                # thêm seed node vào tập kết quả
                related_nodes[node_id] = node

                # check label node thuộc cấp nào, duyệt các node con dựa trên cấp
                label = node.get("label")
                if label is None:
                    logger.warning(
                        f"Node {node_text} (node_id: {node_id}) không có label, bỏ qua."
                    )
                    continue

                high_level_labels = {
                    LegalHierarchyLabels.Document,
                    LegalHierarchyLabels.Part,
                    LegalHierarchyLabels.Chapter,
                }
                low_level_labels = {
                    LegalHierarchyLabels.Section,
                    LegalHierarchyLabels.SubSection,
                    LegalHierarchyLabels.Article,
                    LegalHierarchyLabels.Clause,
                    LegalHierarchyLabels.Point,
                }

                if label in high_level_labels:
                    logger.info(
                        f"Node {node_text} (node_id: {node_id}) là cấp cao ({label})"
                    )
                elif label in low_level_labels:
                    logger.info(
                        f"Node {node_text} (node_id: {node_id}) là cấp thấp ({label})"
                    )
                    # gom các node liên quan (cha, con, con cháu) và quan hệ pháp lý
                    seed_ids = [node_id]
                    nodes = self._collect_related_nodes(seed_ids)
                    for n in nodes:
                        nid = n.get("node_id")
                        if not nid:
                            continue
                        if nid in related_nodes:
                            # Bảo toàn metadata truy xuất (score, rank, retrieval_source...) của seed node
                            related_nodes[nid] = {**n, **related_nodes[nid]}
                        else:
                            related_nodes[nid] = n

                    # related relationships
                    legal_relationships = self._collect_legal_relationships(seed_ids)
                    related_relationships.extend(legal_relationships)

                    logger.info(f"Quan hệ pháp lý liên quan: {legal_relationships}.")

            # Gom bổ sung các document tương ứng cho tất cả các node trong related_nodes
            for n in list(related_nodes.values()):
                doc_id = n.get("document_id")
                if doc_id and doc_id not in related_documents:
                    doc = self._legal_graph_service.get_document(doc_id)
                    if doc:
                        related_documents[doc_id] = doc

            # Format output chuẩn 6-key
            return {
                "input": query_text,
                "extracted_hierarchy": None,
                "node_information": None,
                "related_documents": [
                    self.format_node(doc) for doc in related_documents.values()
                ],
                "related_nodes": [
                    self.format_node(node) for node in related_nodes.values()
                ],
                "relationships": self._build_relationships(
                    nodes=list(related_nodes.values()),
                    legal_relationships=related_relationships,
                ),
            }

    def _collect_related_nodes(self, seed_ids: list[str]) -> list[dict[str, Any]]:
        """Gom node đích/seed + cha + con + con cháu, khử trùng theo node_id.

        Node `Document` bị loại khỏi `related_nodes` vì đã phản ánh trong `related_documents`.

        Args:
            seed_ids: Danh sách node_id gốc đã chạm được.

        Returns:
            Danh sách node theo thứ tự: seed trước, rồi cha, con, con cháu.
        """
        collected: dict[str, dict[str, Any]] = {}

        def add(node: Optional[dict[str, Any]]) -> None:
            """Thêm node vào tập kết quả nếu hợp lệ và chưa có."""
            if not node:
                return
            node_id = node.get("node_id")
            if not node_id or node_id in collected:
                return
            if node.get("label") == "Document":
                return
            collected[node_id] = node

        for seed_id in seed_ids:
            if not seed_id:
                continue
            add(self._legal_graph_service.get_node_by_id(seed_id))
            for ancestor in self._legal_graph_service.get_breadcrumbs(seed_id):
                add(ancestor)
            for child in self._legal_graph_service.get_children(seed_id):
                add(child)
            for descendant in self._legal_graph_service.get_descendants(
                seed_id, max_depth=5, limit=200
            ):
                add(descendant)

        return list(collected.values())

    def _collect_legal_relationships(
        self, seed_ids: list[str]
    ) -> list[tuple[str, dict[str, Any]]]:
        """Lấy quan hệ pháp lý của từng seed, gắn kèm node gốc để định hướng cạnh.

        Args:
            seed_ids: Danh sách node_id gốc.

        Returns:
            Danh sách cặp (node_id gốc, bản ghi quan hệ).
        """
        relationships: list[tuple[str, dict[str, Any]]] = []
        for seed_id in seed_ids:
            if not seed_id:
                continue
            for relationship in self._legal_graph_service.get_related_laws(
                seed_id, limit=50
            ):
                relationships.append((seed_id, relationship))
        return relationships

    def _collect_related_documents(
        self,
        document_ids: list[str],
        nodes: list[dict[str, Any]],
        legal_relationships: list[tuple[str, dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """Gom provenance các văn bản liên quan (văn bản resolve + văn bản của node/quan hệ).

        Args:
            document_ids: Document_id khởi điểm (văn bản resolve được).
            nodes: Các node đã gom.
            legal_relationships: Các quan hệ pháp lý đã gom.

        Returns:
            Danh sách provenance đã chuẩn hoá, khử trùng theo document_id.
        """
        collected: dict[str, dict[str, Any]] = {}

        def add_document(document_id: Optional[str]) -> None:
            """Thêm provenance của một văn bản nếu chưa có."""
            if not document_id or document_id in collected:
                return
            provenance = self._legal_graph_service.get_document_provenance(document_id)
            if provenance:
                collected[document_id] = provenance

        for document_id in document_ids:
            add_document(document_id)
        for node in nodes:
            add_document(node.get("document_id"))
        for _, relationship in legal_relationships:
            for key in ("target_node", "source_node", "related_node"):
                related_node = relationship.get(key)
                if related_node:
                    add_document(related_node.get("document_id"))

        return list(collected.values())

    def _build_relationships(
        self,
        nodes: list[dict[str, Any]],
        legal_relationships: list[tuple[str, dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """Gộp quan hệ cấu trúc (CONTAINS) và quan hệ pháp lý thành mảng phẳng.

        Args:
            nodes: Các node đã gom (dùng `parent_id` để suy cạnh CONTAINS).
            legal_relationships: Các cặp (node gốc, bản ghi quan hệ pháp lý).

        Returns:
            Danh sách quan hệ {from_node_id, to_node_id, relationship_type}, khử trùng lặp.
        """
        collected: dict[tuple[str, str, str], dict[str, Any]] = {}

        def add(
            from_node_id: Optional[str],
            to_node_id: Optional[str],
            relationship_type: Optional[str],
        ) -> None:
            """Thêm một cạnh nếu đủ thông tin và chưa tồn tại."""
            if not from_node_id or not to_node_id or not relationship_type:
                return
            key = (from_node_id, relationship_type, to_node_id)
            if key in collected:
                return
            collected[key] = {
                "from_node_id": from_node_id,
                "to_node_id": to_node_id,
                "relationship_type": relationship_type,
            }

        # Cạnh cấu trúc CONTAINS suy từ parent_id của các node đã gom.
        for node in nodes:
            add(node.get("parent_id"), node.get("node_id"), "CONTAINS")

        # Cạnh quan hệ pháp lý (REFERENCES, IMPLEMENTS, INTERPRETED_BY...).
        for root_id, relationship in legal_relationships:
            relationship_type = relationship.get("relation_type")
            if relationship.get("direction") == "INCOMING":
                source = relationship.get("source_node") or {}
                add(source.get("node_id"), root_id, relationship_type)
            else:
                target = relationship.get("target_node") or {}
                add(root_id, target.get("node_id"), relationship_type)

        return list(collected.values())
