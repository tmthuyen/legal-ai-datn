"""Unit tests cho QdrantVectorStore adapter."""

import math
import shutil
import tempfile

import pytest

from src.vector.qdrant_store import QdrantVectorStore


@pytest.fixture
def temp_qdrant_dir():
    d = tempfile.mkdtemp(prefix="test_qdrant_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_qdrant_store_create_and_count(temp_qdrant_dir):
    store = QdrantVectorStore(
        location=temp_qdrant_dir,
        collection_name="test_col",
        model_name="test_model",
        dimension=4,
        create=True,
    )
    assert store.count() == 0
    store.close()


def test_qdrant_store_upsert_and_query(temp_qdrant_dir):
    store = QdrantVectorStore(
        location=temp_qdrant_dir,
        collection_name="test_articles",
        model_name="test_model",
        dimension=4,
        create=True,
    )

    ids = ["BLDS_2015_D1", "LUAT_HNGD_2014_D2"]
    vectors = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]]
    documents = ["Enriched Điều 1 BLDS", "Enriched Điều 2 HNGĐ"]
    metadatas = [
        {
            "node_id": "BLDS_2015_D1",
            "label": "Article",
            "document_id": "BLDS_2015",
            "number": "1",
        },
        {
            "node_id": "LUAT_HNGD_2014_D2",
            "label": "Article",
            "document_id": "LUAT_HNGD_2014",
            "number": "2",
        },
    ]

    store.upsert(ids, vectors, documents, metadatas)
    assert store.count() == 2

    # Query gần với Điều 1
    hits = store.query([1.0, 0.0, 0.0, 0.0], top_k=2)
    assert len(hits) == 2
    assert hits[0]["node_id"] == "BLDS_2015_D1"
    assert hits[0]["score"] > 0.99
    assert hits[0]["metadata"]["document_id"] == "BLDS_2015"

    store.close()


def test_qdrant_store_query_with_document_filter(temp_qdrant_dir):
    store = QdrantVectorStore(
        location=temp_qdrant_dir,
        collection_name="test_filter",
        model_name="test_model",
        dimension=4,
        create=True,
    )

    ids = ["BLDS_2015_D1", "LUAT_HNGD_2014_D1"]
    vectors = [[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]
    documents = ["Text 1", "Text 2"]
    metadatas = [
        {"node_id": "BLDS_2015_D1", "label": "Article", "document_id": "BLDS_2015"},
        {
            "node_id": "LUAT_HNGD_2014_D1",
            "label": "Article",
            "document_id": "LUAT_HNGD_2014",
        },
    ]
    store.upsert(ids, vectors, documents, metadatas)

    # Filter chỉ lấy LUAT_HNGD_2014
    hits = store.query([1.0, 0.0, 0.0, 0.0], top_k=5, document_filter="LUAT_HNGD_2014")
    assert len(hits) == 1
    assert hits[0]["node_id"] == "LUAT_HNGD_2014_D1"

    store.close()


def test_qdrant_store_validates_vectors(temp_qdrant_dir):
    store = QdrantVectorStore(
        location=temp_qdrant_dir,
        collection_name="test_val",
        model_name="test_model",
        dimension=4,
        create=True,
    )

    # Wrong dimension
    with pytest.raises(ValueError, match="Vector sai dimension"):
        store._validate_vectors([[1.0, 2.0]])

    # NaN value
    with pytest.raises(ValueError, match="Vector sai dimension hoặc chứa NaN"):
        store._validate_vectors([[1.0, 2.0, float("nan"), 4.0]])

    # Zero norm
    with pytest.raises(ValueError, match="Cosine không xác định cho vector zero"):
        store._validate_vectors([[0.0, 0.0, 0.0, 0.0]])

    store.close()


def test_qdrant_store_get(temp_qdrant_dir):
    store = QdrantVectorStore(
        location=temp_qdrant_dir,
        collection_name="test_get",
        model_name="test_model",
        dimension=4,
        create=True,
    )

    ids = ["BLDS_2015_D1"]
    vectors = [[0.5, 0.5, 0.5, 0.5]]
    documents = ["Doc 1"]
    metadatas = [
        {"node_id": "BLDS_2015_D1", "label": "Article", "document_id": "BLDS_2015"}
    ]
    store.upsert(ids, vectors, documents, metadatas)

    data = store.get(ids=["BLDS_2015_D1"])
    assert data["ids"] == ["BLDS_2015_D1"]
    assert data["documents"] == ["Doc 1"]

    all_data = store.get()
    assert "BLDS_2015_D1" in all_data["ids"]

    store.close()
