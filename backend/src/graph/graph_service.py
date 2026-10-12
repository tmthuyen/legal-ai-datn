
# from typing import Any

# from src.graph.graph_repository import LegalGraphRepository, LegalLabels


# class LegalGraphService:
#     def __init__(self, repository: LegalGraphRepository):
#         self._repository = repository

#     def get_all_legal_nodes(
#         self, 
#         limit: int = 100, 
#         order_by: str | None = None
#     ) -> list[dict[str, Any]]:
#         return self._repository.find_all(
#             label=LegalLabels.LegalNode, 
#             limit=limit, 
#             order_by=order_by
#         )
        
#     def get_all_legal_relationships(
#         self, 
#         limit: int = 100
#     ) -> list[dict[str, Any]]:
#         return self._repository.get_all_relationships(
#             label=LegalLabels.LegalNode, 
#             limit=limit
#         )
        
#     def get_relationships_by_node_and_type(
#         self, 
#         node_id: str, 
#         relationship_type: str, 
#         limit: int = 100
#     ) -> list[dict[str, Any]]:
#         return self._repository.get_node_by_id_and_relationship_type(
#             label=LegalLabels.LegalNode,
#             node_id=node_id,
#             relationship_type=relationship_type, 
#             limit=limit
#         )
        
#     def get_relationships_by_node(
#         self, 
#         node_id: str,  
#         limit: int = 100
#     ) -> list[dict[str, Any]]:
#         return self._repository.get_relationships_by_node(
#             label=LegalLabels.LegalNode,
#             node_id=node_id, 
#             limit=limit
#         )