import json
from typing import Any, Optional

from src.common.constants import LegalHierarchyLabels, MinimumScoreThresholds
from src.common.custom_exception import CustomException
from src.common.schemas import LegalHierarchy
from src.graph.graph_service import LegalGraphService
from src.retrieval.graph_traverse import GraphTraverse
from src.retrieval.hybrid import HybridSearcher
from src.retrieval.legal_query_extractor import LegalQueryExtractor
from src.retrieval.semantic import SemanticSearcher
from src.utils.logger import setup_logger

logger = setup_logger("retrieval_service", filename="retrieval_service.log")


class RetrievalService:
    """Điều phối hai luồng Retrieval: theo phân cấp và Hybrid + Graph."""

    def __init__(
        self,
        legal_query_extractor: LegalQueryExtractor,
        legal_graph_service: LegalGraphService,
        semantic_service: SemanticSearcher,
        hybrid_service: HybridSearcher,
        graph_traverse: GraphTraverse,
    ):
        """Khởi tạo orchestrator.

        Args:
            legal_graph_service: Service truy vấn đồ thị.
            legal_query_extractor: Bộ parse câu hỏi -> phân cấp.
            semantic_service: Service tìm kiếm ngữ nghĩa.
            hybrid_service: Service tìm kiếm kết hợp Hybrid (Semantic + BM25).
            graph_traverse: Bộ duyệt đồ thị; mặc định tự khởi tạo từ graph service.
        """
        # Check parameter
        if not legal_query_extractor:
            logger.warning("Thiếu legal_query_extractor khi khởi tạo RetrievalService")
        if (
            not legal_graph_service
            or not semantic_service
            or not hybrid_service
            or not graph_traverse
        ):
            raise CustomException(
                message="Thiếu tham số khởi tạo RetrievalService",
                status_code=500,
                error_code="INTERNAL_SERVER_ERROR",
            )

        self._semantic_service = semantic_service
        self._legal_graph_service = legal_graph_service
        self._extractor = legal_query_extractor
        self._hybrid_service = hybrid_service
        self._graph_traverse = graph_traverse

        logger.info("Khởi tạo RetrievalService thành công.")

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

                related_nodes[node_id] = node

                logger.info(
                    "Gom các node liên quan (cha, con, con cháu) và quan hệ pháp lý"
                )
                for related_node in self._graph_traverse.traverse_node_hierarchy(
                    node_id
                ):
                    related_nodes[related_node["node_id"]] = related_node

                legal_relationships = [
                    (node_id, relation)
                    for relation in self._graph_traverse.traverse_legal_relations(
                        node_id
                    )
                ]
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
                "relationships": self._graph_traverse.build_flat_relationships(
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
            related_documents_found = search_nodes.get("related_documents", [])

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
                    nodes = self._graph_traverse.traverse_node_hierarchy(node_id)
                    for n in nodes:
                        nid = n.get("node_id")
                        if not nid:
                            continue
                        if nid in related_nodes:
                            # Bảo toàn metadata truy xuất (score, rank, retrieval_source...) của seed node
                            related_nodes[nid] = {**n, **related_nodes[nid]}
                        else:
                            related_nodes[nid] = n

                    legal_relationships = [
                        (node_id, relation)
                        for relation in self._graph_traverse.traverse_legal_relations(
                            node_id
                        )
                    ]
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
                "relationships": self._graph_traverse.build_flat_relationships(
                    nodes=list(related_nodes.values()),
                    legal_relationships=related_relationships,
                ),
            }

    def retrieve_hybrid_and_graph(
        self,
        query_text: str,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """Truy vấn Hybrid Search rồi mở rộng đồ thị, không dùng LLM.

        Args:
            query_text: Câu hỏi người dùng.
            top_k: Số seed node lấy từ Hybrid/Semantic Search.

        Returns:
            {
                "input": query_text,
                "relevant_laws": list[dict],  # seed node kèm relationships lồng nhau
                "relevant_documents": list[dict],  # văn bản gốc chứa các node trên
            }
        """
        logger.info(f"Nhận câu hỏi (hybrid + graph): {query_text}")

        searcher = (
            self._hybrid_service
            if self._hybrid_service is not None
            else self._semantic_service
        )
        search_result = searcher.search(query=query_text, top_k=top_k)

        latency_info = {
            "total_found": search_result.get("total_found", 0),
            "search_time_ms": search_result.get("search_time_ms", 0.0),
            "semantic_time_ms": search_result.get("semantic_time_ms", 0.0),
            "bm25_time_ms": search_result.get("bm25_time_ms", 0.0),
        }

        logger.info("Hybrid Latency: %s", json.dumps(latency_info, ensure_ascii=False))

        # log keys
        logger.info(
            "Hybrid Search Result Keys: %s",
            json.dumps(list(search_result.keys()), ensure_ascii=False),
        )

        seed_nodes: list[dict] = search_result.get("results") or search_result.get(
            "related_nodes", []
        )

        if not seed_nodes:
            logger.warning("Không tìm thấy seed node nào từ Hybrid Search.")
            return {
                "input": query_text,
                "relevant_laws": [],
                "relevant_documents": [],
            }

        # related nodes keys
        logger.info(
            "Hybrid Search Related Nodes Keys: %s",
            json.dumps(
                seed_nodes[0].keys() if seed_nodes else [],
                ensure_ascii=False,
            ),
        )

        relevant_laws, relevant_documents = self._graph_traverse.build_relevant_laws(
            seed_nodes
        )
        logger.info(
            "Hybrid + Graph hoàn tất: %d law nodes, %d documents.",
            len(relevant_laws),
            len(relevant_documents),
        )

        return {
            "input": query_text,
            "relevant_laws": relevant_laws,
            "relevant_documents": relevant_documents,
        }
