"""Persistent cosine store, sử dụng vector do ứng dụng cung cấp."""

import math

import chromadb
from chromadb.errors import NotFoundError

from src.utils.logger import setup_logger

logger = setup_logger("chroma_store", "chroma_store.log")


class ChromaVectorStore:
    """Lưu Article vectors với ID trùng node_id và kiểm tra embedding space."""

    def __init__(self, path, collection_name, model_name, dimension, create=True):
        """Mở collection; từ chối metric/model/dimension khác, không reset ngầm."""
        self.client = chromadb.PersistentClient(path=str(path))
        self.dimension = dimension
        self.name = collection_name
        metadata = {"embedding_model": model_name, "dimension": dimension}
        try:
            self.collection = self.client.get_collection(
                collection_name, embedding_function=None
            )
        except NotFoundError:
            if not create:
                self.client.close()
                raise
            self.collection = self.client.create_collection(
                collection_name,
                embedding_function=None,
                metadata=metadata,
                configuration={"hnsw": {"space": "cosine"}},
            )
        configuration = self.collection.configuration
        if (configuration.get("hnsw") or {}).get("space") != "cosine":
            self.client.close()
            raise ValueError("Collection phải dùng cosine; không tự đổi metric.")
        if any(
            (self.collection.metadata or {}).get(k) != v for k, v in metadata.items()
        ):
            self.client.close()
            raise ValueError("Collection khác model/dimension; dùng collection riêng.")

    def _validate_vectors(self, vectors):
        """Từ chối vector sai chiều, không hữu hạn hoặc có norm bằng không."""
        for vector in vectors:
            if len(vector) != self.dimension or not all(
                math.isfinite(v) for v in vector
            ):
                raise ValueError("Vector sai dimension hoặc chứa NaN/Inf.")
            if not any(v != 0 for v in vector):
                raise ValueError("Cosine không xác định cho vector zero.")

    def upsert(self, ids, embeddings, documents, metadatas):
        """Ghi idempotent, giữ nguyên enriched text ứng với từng vector."""
        if not ids or len(set(ids)) != len(ids):
            raise ValueError("Danh sách IDs rỗng hoặc trùng.")
        if not (len(ids) == len(embeddings) == len(documents) == len(metadatas)):
            raise ValueError("Số lượng record không khớp.")
        self._validate_vectors(embeddings)
        for nid, meta, text in zip(ids, metadatas, documents):
            if meta.get("node_id") != nid or meta.get("label") != "Article":
                raise ValueError("Metadata phải trỏ đúng Article node_id.")
            if not text.strip() or not meta.get("document_id"):
                raise ValueError("Thiếu enriched text/document_id.")
        size = self.client.get_max_batch_size()
        for start in range(0, len(ids), size):
            end = start + size
            self.collection.upsert(
                ids=ids[start:end],
                embeddings=embeddings[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )
        logger.info("Upsert %d Article vectors vào %s", len(ids), self.name)

    def query(self, vector, top_k=5, document_filter=None):
        """Lọc trước top-k; score=(1+cosine)/2=1-distance/2, càng cao càng tốt."""
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k phải là số nguyên dương.")
        self._validate_vectors([vector])
        count = self.count()
        if not count:
            return []
        where = {"document_id": {"$eq": document_filter}} if document_filter else None
        result = self.collection.query(
            query_embeddings=[vector],
            n_results=min(top_k, count),
            where=where,
            include=["distances", "metadatas"],
        )
        return [
            {
                "node_id": nid,
                "score": max(0.0, min(1.0, 1.0 - float(distance) / 2)),
                "metadata": meta,
            }
            for nid, distance, meta in zip(
                result["ids"][0], result["distances"][0], result["metadatas"][0]
            )
        ]

    def count(self):
        """Đếm record trong collection."""
        return self.collection.count()

    def close(self):
        """Đóng persistent client và giải phóng file handles."""
        self.client.close()

    def get(self, ids=None):
        """Đọc record phục vụ audit mà không tự sinh embedding."""
        return self.collection.get(
            ids=ids, include=["documents", "metadatas", "embeddings"]
        )
