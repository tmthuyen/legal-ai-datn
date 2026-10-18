# backend/tests/conftest.py
import pytest
from unittest.mock import MagicMock
from src.graph.neo4j_client import Neo4jClient
from src.graph.graph_repository import LegalGraphRepository
from src.graph.graph_service import LegalGraphService

@pytest.fixture
def mock_neo4j_client():
    """Tạo mock Neo4jClient không cần kết nối mạng."""
    client = MagicMock(spec=Neo4jClient)
    return client

@pytest.fixture
def mock_repo(mock_neo4j_client):
    """Repository chạy với mock client."""
    return LegalGraphRepository(db=mock_neo4j_client)

@pytest.fixture
def mock_service(mock_repo):
    """Service chạy với mock repo."""
    return LegalGraphService(repository=mock_repo)
