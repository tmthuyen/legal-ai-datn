import json
import sys
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from regex import E

from src.common.constants import LegalHierarchyLabels, MinimumScoreThresholds
from src.common.custom_exception import CustomException
from src.common.schemas import LegalHierarchy
from src.graph.graph_service import LegalGraphService
from src.models.legal_model import BaseLegalModel
from src.retrieval.legal_query_extractor import LegalQueryExtractor
from src.retrieval.semantic import SemanticSearcher
from src.utils.logger import setup_logger

logger = setup_logger("retrieval_service", filename="retrieval_service.log")


class RetrievalService:
    """Điều phối pipeline Retrieval V1 và dựng output 6 key theo đặc tả."""

    def __init__(
        self,
        legal_query_extractor: LegalQueryExtractor,
        legal_graph_service: LegalGraphService,
        semantic_service: SemanticSearcher,
    ):
        """Khởi tạo orchestrator.

        Args:
            legal_graph_service: Service truy vấn đồ thị.
            legal_query_extractor: Bộ parse câu hỏi -> phân cấp.
            semantic_service: Service tìm kiếm ngữ nghĩa.
            legal_model: Mô hình suy luận luật.
        """
        self._semantic_service = semantic_service
        self._legal_graph_service = legal_graph_service
        self._extractor = legal_query_extractor

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

        node_type = hierarchy.get_node_type()
        # Nếu type (label) là document thì search cả query
        is_document_type = node_type == LegalHierarchyLabels.Document

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
                document_id = doc.get("document_id") or doc.get("node_id")
                document_name = doc.get("title")
                score = doc.get("score", 0)

                logger.info(
                    f"Kiểm tra document: {document_name} (document_id: {document_id}) (score: {score})"
                )

                if document_id is None:
                    continue

                if score < MinimumScoreThresholds.SEMANTIC_SEARCH_DOCUMENTS:
                    logger.warning(
                        f"Document {document_name} (document_id: {document_id}) bị loại bỏ do score thấp ({score} < {MinimumScoreThresholds.SEMANTIC_SEARCH_DOCUMENTS})."
                    )
                    continue

                node_id = hierarchy.get_node_id_from_document_id(
                    document_id=document_id
                )
                logger.info(
                    f"Tạo node_id với document_id từ phân cấp: {node_id} (document_id: {document_id})"
                )

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

                related_documents[document_id] = doc

            # Nếu không có node và document nào được tìm thấy, return
            if (not related_nodes or len(related_nodes) == 0) and (
                not related_documents or len(related_documents) == 0
            ):
                logger.warning(
                    "Không tìm thấy node hoặc document nào liên quan từ phân cấp parse được."
                )
                return EMPTY_RESULT

            logger.info(
                f"Tổng hợp kết quả: {len(related_nodes)} nodes, {len(related_documents)} documents, {len(related_relationships)} relationships."
            )

            # =======================================================
            # lọc các node liên quan nhất với query_text bằng semantic search, giảm số lượng node cần xử lý bước sau
            ## CHƯA CẦN ĐẾN, GIAI ĐOẠN SAU CÓ THỂ XỬ LÝ Ở ĐÂY
            # =======================================================

            # Lọc document chính xác nhất của node, không loại doc liên quan
            logger.info(
                f"Lọc document chính xác nhất của node, không loại doc liên quan"
            )
            top_score = 0
            for doc in semantic_search_documents:
                score = doc.get("score", 0)
                if score > top_score:
                    top_score = score
                    hierarchy.document = doc.get("title")

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

        # Nếu không có phân cấp: semantic search (V2) hoặc fallback search (V1) để tìm node liên quan.
        if not has_hierarchy or is_document_type:
            logger.info(
                f"Không tìm thấy phân cấp trong câu hỏi, sẽ tìm kiếm node liên quan bằng semantic search."
            )

            # Tìm kiếm toàn graph theo semantic search
            semantic_search_nodes = self._semantic_service.search(
                query=query_text,
                top_k=10,
            )

            if not semantic_search_nodes or "results" not in semantic_search_nodes:
                logger.warning(
                    "Không tìm thấy node hoặc document nào liên quan từ semantic search."
                )
                return EMPTY_RESULT

            # semantic_results = semantic_search_nodes.get("results", {})
            related_nodes_semantic = semantic_search_nodes.get(
                "related_nodes",
            )
            related_documents_semantic = semantic_search_nodes.get(
                "related_documents", []
            )

            logger.info(
                f"Kết quả tìm kiếm ngữ nghĩa: {len(related_nodes_semantic)} nodes, {len(related_documents_semantic)} documents."
            )

            if not related_nodes_semantic and not related_documents_semantic:
                logger.warning(
                    "Không tìm thấy node hoặc document nào liên quan từ semantic search."
                )
                return EMPTY_RESULT

            # Duyệt kết quả semantic để tìm kiếm thêm node liên quan
            # Kết quả semantic thu hẹp phạm vi node cần kiểm tra
            # nhưng có thể chưa đủ thông tin cần thiết
            for node in related_nodes_semantic:
                node_id = node.get("node_id")
                if not node_id:
                    logger.error(f"Node không có node_id, bỏ qua: {node}")
                    continue

                # check score threshold
                score = node.get("score", 0)
                node_text = (
                    node.get("title")
                    or node.get("text")
                    or node.get("full_text")
                    or "Unknown"
                )
                if score < MinimumScoreThresholds.SEMANTIC_SEARCH_NODES:
                    logger.warning(
                        f"Node {node_text} (node_id: {node_id}) bị loại bỏ do score thấp ({score} < {MinimumScoreThresholds.SEMANTIC_SEARCH_NODES})."
                    )
                    continue

                # thêm node vào tập kết quả
                related_nodes[node_id] = node

                # check label node thuộc cấp nào, duyệt các node con dựa trên cấp
                # tránh mở rộng qua nhiếu node con khi node cấp cao (Document, Part, Chapter) có nhiều con
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
                    logger.info(
                        f"Duyệt thông minh và lọc các node con liên quan câu hỏi nhất"
                    )
                    # Duyệt lai graph và sắp xếp mực đô liên quan các node hậu duệ

                elif label in low_level_labels:
                    logger.info(
                        f"Node {node_text} (node_id: {node_id}) là cấp thấp ({label})"
                    )
                    # gom các node liên quan (cha, con, con cháu) và quan hệ pháp lý
                    seed_ids = [node_id]
                    nodes = self._collect_related_nodes(seed_ids)
                    for n in nodes:
                        related_nodes[n["node_id"]] = n

                    # related relationships
                    legal_relationships = self._collect_legal_relationships(seed_ids)
                    related_relationships.extend(legal_relationships)

        # ======================================================
        # Xử lý các node và những quan hệ để gom đủ thông tin trả về
        # =====================================================
        logger.info(
            "Chưa triển khai gom các node liên quan và quan hệ pháp lý từ semantic search, sẽ triển khai ở giai đoạn sau."
        )

        # Format output
        return {
            "input": query_text,
            "extracted_hierarchy": None,
            "node_information": None,
            "related_documents": [
                self.format_node(doc) for doc in related_documents_semantic
            ],
            "related_nodes": [
                self.format_node(node) for node in related_nodes_semantic
            ],
            "relationships": [],
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
