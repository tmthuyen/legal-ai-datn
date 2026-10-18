# backend/tests/unit/test_graph_service.py

def test_resolve_target_node_finds_article(mock_service, mock_neo4j_client):
    """Kiểm tra khi target có Điều thì gọi đúng query tìm Điều."""
    # Arrange: Giả lập Neo4j trả về node Điều 27
    mock_neo4j_client.execute_read.return_value = [
        {"a": {"node_id": "BLDS_2015_D27", "number": 27, "type": "Article"}, "labels": ["Article"]}
    ]

    # Act
    target = {"article": 27, "clause": None, "point": None}
    node = mock_service.resolve_target_node(document_id="BLDS_2015", target=target)

    # Assert
    assert node is not None
    assert node["node_id"] == "BLDS_2015_D27"
    assert node["number"] == 27
    # Xác nhận mock đã được gọi
    assert mock_neo4j_client.execute_read.called
