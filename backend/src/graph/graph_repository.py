
from typing import Any

from src.graph.neo4j_client import Neo4jClient
from src.utils.logger import setup_logger

logger = setup_logger(name="graph_repository", filename="graph_repository.log")

class LegalLabels:
    LegalNode = 'LegalNode'
    
class LegalHierarchyLabels:
    Document = 'Document'       # Van ban
    Part = 'Part'               # Phan
    Chapter = 'Chapter'         # Chuong
    Section = 'Section'         # Muc 
    SubSection = 'SubSection'   # Tieu muc
    Article = 'Article'         # Dieu
    Clause = 'Clause'           # Khoan
    Point = 'Point'             # Diem
    
    
class LegalRelationshipTypes:
    RELATED_TO = 'RELATED_TO' # lien quan
    CONTAINS = 'CONTAINS'       # chua
    REFERENCES = 'REFERENCES'   # tham chieu
    IMPLEMENTS = 'IMPLEMENTS'   # thuc hien
    INTERPRETED_BY = 'INTERPRETED_BY' # giai thich bo sung
    AMENDS = 'AMENDS'           # sua doi
    REPLACES = 'REPLACES'         # thay the    

class BaseGraphRepository:
    def __init__(self, db: Neo4jClient):
        self._db = db

    def find_all(
        self,
        label: str,
        limit: int = 100,
        order_by: str | None = None,
    ) -> list[dict[str, Any]]:
        
        logger.info(f"Finding all nodes with label '{label}' and limit {limit}...")

        query = f"""
        MATCH (n:{label})
        RETURN n
        ORDER BY n[$order_by] ASC
        LIMIT $limit
        """

        rows = self._db.execute_read(
            query,
            {"limit": limit, "order_by": order_by},
        )
        
        logger.info(f"Found {len(rows)} nodes with label '{label}'.")

        return [
            dict(row["n"])
            for row in rows
        ]
        
class LegalGraphRepository(BaseGraphRepository):
    
    # relationships
    def get_all_relationships(
        self,
        label: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        
        logger.info(f"Getting all relationships' with limit {limit}...")

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

        rows = self._db.execute_read(
            query,
            {"limit": limit},
        )
        
        logger.info(f"Found {len(rows)} relationships.")
        
        # key
        logger.info(f"Keys: {rows[0].keys() if rows else 'No rows found'}") 

        return [
            {
                "source_id": row["source_id"],
                "relation_type": row["relation_type"],
                "target_id": row["target_id"],
                "properties": row["properties"],
            }
            for row in rows
        ]
        
    def get_relationships_by_node(
        self,
        label: str,
        node_id: str, 
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        
        logger.info(f"Getting relationships for node '{node_id}' with limit {limit}...")

        query = f"""
        MATCH (n:{label})-[r]->(m:{label})
        WHERE n.id = $node_id
        RETURN r, m
        LIMIT $limit
        """

        rows = self._db.execute_read(
            query,
            {"node_id": node_id, "limit": limit},
        )
        
        logger.info(f"Found {len(rows)} relationships for node '{node_id}'.")

        return [
            {
                "relationship": dict(row["r"]),
                "related_node": dict(row["m"]),
            }
            for row in rows
        ]
        
    # get node by id and relationship type
    def get_node_by_id_and_relationship_type(
        self,
        label: str,
        node_id: str,
        relationship_type: str,
        limit: int = 100,
    ) -> dict[str, Any] | None:
        
        logger.info(f"Getting node '{node_id}' with relationships of type '{relationship_type}' and limit {limit}...")

        query = f"""
        MATCH (n:{label})-[r:{relationship_type}]->(m:{label})
        WHERE n.id = $node_id
        RETURN n, r, m
        LIMIT $limit
        """

        rows = self._db.execute_read(
            query,
            {"node_id": node_id, "limit": limit},
        )
        
        if not rows:
            logger.info(f"No relationships found for node '{node_id}' with type '{relationship_type}'.")
            return None

        logger.info(f"Found {len(rows)} relationships for node '{node_id}' with type '{relationship_type}'.")

        node_data = dict(rows[0]["n"])
        relationships = [
            {
                "relationship": dict(row["r"]),
                "related_node": dict(row["m"]),
            }
            for row in rows
        ]

        return {
            "node": node_data,
            "relationships": relationships,
        }