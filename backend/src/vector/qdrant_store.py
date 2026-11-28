"""Persistent cosine vector store dùng Qdrant, hỗ trợ cả local path và server URL."""

import json
import math
import pathlib
import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from src.utils.logger import setup_logger

logger = setup_logger("qdrant_store", "qdrant_store.log")

NAMESPACE_QDRANT = uuid.NAMESPACE_DNS


class _QdrantCollectionProxy:
    """Proxy tương thích với interface collection.metadata và collection.modify của Chroma."""

    def __init__(self, store: "QdrantVectorStore"):
        self._store = store

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._store.metadata

    def modify(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        if metadata:
            self._store.update_metadata(metadata)


class QdrantVectorStore:
    """Lưu Article vectors trên Qdrant với UUID deterministically sinh từ node_id."""

    def __init__(
        self,
        location: Any,
        collection_name: str,
        model_name: str,
        dimension: int,
        create: bool = True,
    ):
        """Khởi tạo QdrantVectorStore.

        Args:
            location: Đường dẫn Path/str tới thư mục lưu local hoặc URL server (vd: http://localhost:6333).
            collection_name: Tên collection.
            model_name: Tên model embedding để kiểm tra tính nhất quán.
            dimension: Số chiều vector (vd: 1024).
            create: Có tạo collection mới nếu chưa tồn tại hay không.
        """
        loc_str = str(location)
        if loc_str.startswith("http://") or loc_str.startswith("https://"):
            self.client = QdrantClient(url=loc_str)
            self._meta_file = None
        else:
            p = pathlib.Path(loc_str)
            p.mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=str(p))
            self._meta_file = p / f"{collection_name}_meta.json"

        self.dimension = dimension
        self.name = collection_name
        self.model_name = model_name
        self.collection = _QdrantCollectionProxy(self)

        initial_meta = {"embedding_model": model_name, "dimension": dimension}

        exists = self.client.collection_exists(collection_name)
        if not exists:
            if not create:
                self.client.close()
                raise ValueError(f"Collection '{collection_name}' không tồn tại.")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )
            self._save_metadata(initial_meta)
        else:
            col_info = self.client.get_collection(collection_name)
            params = col_info.config.params.vectors
            if isinstance(params, dict):
                size = params.get("size")
                dist = params.get("distance")
            else:
                size = getattr(params, "size", None)
                dist = getattr(params, "distance", None)

            if size != dimension:
                self.client.close()
                raise ValueError(
                    f"Collection dimension ({size}) không khớp cấu hình ({dimension})."
                )
            if dist not in (Distance.COSINE, "Cosine", "cosine"):
                self.client.close()
                raise ValueError("Collection phải dùng cosine; không tự đổi metric.")

            meta = self.metadata
            if meta.get("embedding_model") and meta["embedding_model"] != model_name:
                self.client.close()
                raise ValueError(
                    f"Collection dùng model '{meta['embedding_model']}', khác model hiện tại '{model_name}'."
                )

    def _meta_filepath(self) -> Optional[pathlib.Path]:
        return self._meta_file

    @property
    def metadata(self) -> Dict[str, Any]:
        """Đọc metadata của collection từ file lưu trữ."""
        if self._meta_file and self._meta_file.exists():
            try:
                with open(self._meta_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Không thể đọc metadata file %s: %s", self._meta_file, e)
        return {"embedding_model": self.model_name, "dimension": self.dimension}

    def _save_metadata(self, meta: Dict[str, Any]) -> None:
        if self._meta_file:
            try:
                with open(self._meta_file, "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning("Không thể ghi metadata file %s: %s", self._meta_file, e)

    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """Cập nhật thêm metadata."""
        current = self.metadata
        current.update(updates)
        self._save_metadata(current)

    def _validate_vectors(self, vectors: List[Any]) -> None:
        """Từ chối vector sai chiều, không hữu hạn hoặc có norm bằng không."""
        for vector in vectors:
            if len(vector) != self.dimension or not all(
                math.isfinite(v) for v in vector
            ):
                raise ValueError("Vector sai dimension hoặc chứa NaN/Inf.")
            if not any(v != 0 for v in vector):
                raise ValueError("Cosine không xác định cho vector zero.")

    def _to_uuid(self, node_id: str) -> str:
        """Chuyển node_id dạng chuỗi sang deterministic UUID chuỗi cho Qdrant."""
        return str(uuid.uuid5(NAMESPACE_QDRANT, node_id))

    def upsert(
        self,
        ids: List[str],
        embeddings: Any,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Ghi idempotent các điểm vector vào Qdrant."""
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

        points = []
        for nid, emb, doc, meta in zip(ids, embeddings, documents, metadatas):
            point_id = self._to_uuid(nid)
            payload = {
                **meta,
                "node_id": nid,
                "document": doc,
            }
            vec = emb.tolist() if hasattr(emb, "tolist") else list(emb)
            points.append(PointStruct(id=point_id, vector=vec, payload=payload))

        batch_size = 500
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(collection_name=self.name, points=batch)

        logger.info(
            "Upsert %d Article vectors vào Qdrant collection %s", len(ids), self.name
        )

    def query(
        self,
        vector: Any,
        top_k: int = 5,
        document_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Lọc trước top-k; chuyển cosine score [-1, 1] sang [0, 1] cho đồng bộ Chroma."""
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k phải là số nguyên dương.")
        self._validate_vectors([vector])
        total_count = self.count()
        if not total_count:
            return []

        query_filter = None
        if document_filter:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_filter),
                    )
                ]
            )

        vec = vector.tolist() if hasattr(vector, "tolist") else list(vector)
        res = self.client.query_points(
            collection_name=self.name,
            query=vec,
            limit=min(top_k, total_count),
            query_filter=query_filter,
            with_payload=True,
        )

        results = []
        for hit in res.points:
            payload = hit.payload or {}
            node_id = payload.get("node_id", "")
            raw_score = float(hit.score)
            normalized_score = max(0.0, min(1.0, (1.0 + raw_score) / 2.0))
            results.append(
                {
                    "node_id": node_id,
                    "score": normalized_score,
                    "metadata": payload,
                }
            )
        return results

    def count(self) -> int:
        """Đếm số lượng record trong collection."""
        try:
            return self.client.count(collection_name=self.name).count
        except Exception:
            return 0

    def close(self) -> None:
        """Đóng client giải phóng tài nguyên."""
        self.client.close()

    def get(self, ids: Optional[List[str]] = None) -> Dict[str, List[Any]]:
        """Đọc record phục vụ audit và migration."""
        if ids is not None:
            point_ids = [self._to_uuid(nid) for nid in ids]
            records = self.client.retrieve(
                collection_name=self.name,
                ids=point_ids,
                with_payload=True,
                with_vectors=True,
            )
        else:
            records, _ = self.client.scroll(
                collection_name=self.name,
                limit=10000,
                with_payload=True,
                with_vectors=True,
            )

        res_ids = []
        res_docs = []
        res_metas = []
        res_embeddings = []
        for r in records:
            p = r.payload or {}
            res_ids.append(p.get("node_id", ""))
            res_docs.append(p.get("document", ""))
            res_metas.append(p)
            res_embeddings.append(r.vector)

        return {
            "ids": res_ids,
            "documents": res_docs,
            "metadatas": res_metas,
            "embeddings": res_embeddings,
        }
