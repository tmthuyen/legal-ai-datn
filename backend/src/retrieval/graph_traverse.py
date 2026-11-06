"""
graph_traverse.py
Duyệt và mở rộng đồ thị tri thức pháp luật phục vụ tầng Retrieval.

Nhiệm vụ:
- Duyệt cây phân cấp (tổ tiên, hậu duệ) của các node hạt giống.
- Duyệt quan hệ pháp lý tham chiếu liên văn bản (REFERENCES, IMPLEMENTS, INTERPRETED_BY...).
- Nhúng mảng relationships trực tiếp vào từng law node.
- Trích xuất tập hợp Document gốc duy nhất chứa toàn bộ các node luật và quan hệ.
"""

from typing import Any, Dict, List, Set, Tuple

from src.graph.graph_service import LegalGraphService
from src.utils.logger import setup_logger

logger = setup_logger("graph_traverse", "graph_traverse.log")

ANCESTOR = "ancestor"
DESCENDANT = "descendant"


class GraphTraverse:
    """Class đảm nhiệm các thuật toán duyệt và cấu trúc hóa quan hệ đồ thị pháp lý."""

    def __init__(self, graph_service: LegalGraphService):
        """Khởi tạo GraphTraverse với LegalGraphService.

        Args:
            graph_service: Service tương tác với Neo4j graph.
        """
        self.graph_service = graph_service

    def traverse_node_hierarchy(
        self, node_id: str, max_depth: int = 5
    ) -> List[Dict[str, Any]]:
        """Duyệt các node phân cấp liên quan: tổ tiên và hậu duệ.

        Args:
            node_id: ID của node hạt giống.
            max_depth: Độ sâu tối đa khi duyệt hậu duệ.

        Returns:
            Danh sách node phân cấp (loại trừ node Document và chính node gốc).
        """
        return [node for _, node in self._collect_hierarchy(node_id, max_depth)]

    def _collect_hierarchy(
        self, node_id: str, max_depth: int = 5
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Gom tổ tiên và hậu duệ kèm vị trí tương đối so với node gốc.

        Args:
            node_id: ID của node hạt giống.
            max_depth: Độ sâu tối đa khi duyệt hậu duệ.

        Returns:
            Danh sách (position, node) với position ∈ {ANCESTOR, DESCENDANT}.
        """
        if not node_id:
            return []

        collected: Dict[str, Tuple[str, Dict[str, Any]]] = {}

        for ancestor in self.graph_service.get_breadcrumbs(node_id) or []:
            self._add_hierarchy_node(collected, ANCESTOR, ancestor)

        descendants = self.graph_service.get_descendants(
            node_id, max_depth=max_depth, limit=100
        )
        for descendant in descendants or []:
            self._add_hierarchy_node(collected, DESCENDANT, descendant)

        return list(collected.values())

    @staticmethod
    def _add_hierarchy_node(
        collected: Dict[str, Tuple[str, Dict[str, Any]]],
        position: str,
        node: Dict[str, Any],
    ) -> None:
        """Thêm node phân cấp nếu hợp lệ, chưa tồn tại và không phải Document."""
        related_id = node.get("node_id")
        if not related_id or related_id in collected:
            return
        if node.get("label") == "Document":
            return
        collected[related_id] = (position, node)

    def traverse_legal_relations(
        self, node_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Duyệt các quan hệ pháp lý ngoài CONTAINS (REFERENCES, IMPLEMENTS...).

        Args:
            node_id: ID của node cần lấy quan hệ.
            limit: Giới hạn số lượng quan hệ trả về.

        Returns:
            Danh sách dict {relation_type, direction, related_node}.
        """
        if not node_id:
            return []

        raw_relations = self.graph_service.get_related_laws(node_id, limit=limit) or []
        legal_relations: List[Dict[str, Any]] = []

        for relation in raw_relations:
            relation_type = relation.get("relation_type")
            if not relation_type or relation_type == "CONTAINS":
                continue

            direction = relation.get("direction", "OUTGOING")
            related_node = (
                relation.get("source_node")
                if direction == "INCOMING"
                else relation.get("target_node")
            )
            if not related_node:
                continue

            legal_relations.append(
                {
                    "relation_type": relation_type,
                    "direction": direction,
                    "related_node": related_node,
                }
            )

        return legal_relations

    def build_relevant_laws(
        self, seed_nodes: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Gắn mảng relationships vào từng law node và gom Document gốc duy nhất.

        Args:
            seed_nodes: Danh sách node luật từ Hybrid Search (kèm score, rank).

        Returns:
            Tuple (relevant_laws, relevant_documents).
        """
        relevant_laws: List[Dict[str, Any]] = []
        document_ids: Set[str] = set()

        for seed in seed_nodes:
            node_id = seed.get("node_id")
            if not node_id:
                continue

            if seed.get("document_id"):
                document_ids.add(seed["document_id"])

            node_relationships: List[Dict[str, Any]] = []
            visited_related_ids: Set[str] = {node_id}

            for position, hierarchy_node in self._collect_hierarchy(node_id):
                related_id = hierarchy_node.get("node_id")
                if related_id in visited_related_ids:
                    continue
                visited_related_ids.add(related_id)

                if hierarchy_node.get("document_id"):
                    document_ids.add(hierarchy_node["document_id"])

                node_relationships.append(
                    {
                        "relation_type": "CONTAINS",
                        "direction": (
                            "INCOMING" if position == ANCESTOR else "OUTGOING"
                        ),
                        "related_node": self._with_citation(hierarchy_node),
                    }
                )

            for relation in self.traverse_legal_relations(node_id):
                related_node = relation.get("related_node") or {}
                related_id = related_node.get("node_id")
                if not related_id or related_id in visited_related_ids:
                    continue
                visited_related_ids.add(related_id)

                if related_node.get("document_id"):
                    document_ids.add(related_node["document_id"])

                node_relationships.append(
                    {
                        "relation_type": relation.get("relation_type"),
                        "direction": relation.get("direction", "OUTGOING"),
                        "related_node": self._with_citation(related_node),
                    }
                )

            relevant_laws.append(
                {
                    **seed,
                    "citation": self.graph_service.get_citation_path(node_id),
                    "relationships": node_relationships,
                }
            )

        relevant_documents: List[Dict[str, Any]] = []
        for document_id in document_ids:
            document = self.graph_service.get_node_by_id(document_id)
            if document:
                relevant_documents.append(self._with_citation(document))

        return relevant_laws, relevant_documents

    def build_flat_relationships(
        self,
        nodes: List[Dict[str, Any]],
        legal_relationships: List[Tuple[str, Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Gộp quan hệ cấu trúc (CONTAINS) và quan hệ pháp lý thành mảng phẳng.

        Args:
            nodes: Các node đã gom (dùng `parent_id` để suy cạnh CONTAINS).
            legal_relationships: Các cặp (node_id gốc, quan hệ đã chuẩn hoá).

        Returns:
            Danh sách quan hệ {from_node_id, to_node_id, relationship_type}.
        """
        collected: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

        def add(
            from_node_id: str | None,
            to_node_id: str | None,
            relationship_type: str | None,
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

        for node in nodes:
            add(node.get("parent_id"), node.get("node_id"), "CONTAINS")

        for root_id, relationship in legal_relationships:
            related_node = relationship.get("related_node") or {}
            relationship_type = relationship.get("relation_type")
            if relationship.get("direction") == "INCOMING":
                add(related_node.get("node_id"), root_id, relationship_type)
            else:
                add(root_id, related_node.get("node_id"), relationship_type)

        return list(collected.values())

    def _with_citation(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Trả bản sao node kèm trích dẫn tuyệt đối."""
        node_id = node.get("node_id")
        citation = self.graph_service.get_citation_path(node_id) if node_id else None
        return {**node, "citation": citation}
