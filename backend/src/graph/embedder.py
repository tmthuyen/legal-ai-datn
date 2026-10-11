"""
embedder.py
Module quản lý Embedding Model cho Legal Knowledge Graph.

Nhiệm vụ:
- Quản lý vòng đời của SentenceTransformer (mặc định BAAI/bge-m3)
- Encode danh sách passages (Article full_text) sang dense vectors (1024-d)
- Encode user query sang dense vector phục vụ Semantic Vector Search
"""

import os
import time
import logging
from typing import List, Optional, Union
import numpy as np
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class NodeEmbedder:
    """
    Wrapper cho SentenceTransformer model, phục vụ sinh vector embedding
    cho các node trong đồ thị và mã hoá query tìm kiếm.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        batch_size: Optional[int] = None,
    ):
        load_dotenv()
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")
        self.device = device or os.getenv("EMBEDDING_DEVICE", "cpu")
        env_batch_size = os.getenv("EMBEDDING_BATCH_SIZE", "8")
        self.batch_size = batch_size if batch_size is not None else int(env_batch_size)
        
        self._model = None
        self._dimension: Optional[int] = None

    def load_model(self):
        """Khởi tạo và nạp model vào RAM/VRAM nếu chưa nạp."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info("Đang nạp embedding model: %s (device=%s)...", self.model_name, self.device)
            start_time = time.time()
            self._model = SentenceTransformer(self.model_name, device=self.device)
            elapsed = time.time() - start_time
            if hasattr(self._model, "get_embedding_dimension"):
                self._dimension = self._model.get_embedding_dimension()
            else:
                self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(
                "Model loaded thành công trong %.2fs (dimension=%d)",
                elapsed,
                self._dimension,
            )
        return self._model

    @property
    def dimension(self) -> int:
        """Kích thước vector embedding (ví dụ 1024 đối với BGE-M3)."""
        if self._dimension is None:
            self.load_model()
        return self._dimension

    def encode_passages(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        show_progress_bar: bool = True,
    ) -> np.ndarray:
        """
        Encode danh sách các đoạn văn bản (full_text của Article).
        
        Args:
            texts: Danh sách chuỗi văn bản cần encode.
            batch_size: Kích thước batch, mặc định lấy từ self.batch_size.
            show_progress_bar: Hiển thị thanh tiến trình tqdm.
            
        Returns:
            np.ndarray ma trận kích thước (N, dimension) với chuẩn L2 (cosine ready).
        """
        model = self.load_model()
        bs = batch_size or self.batch_size
        
        # Kiểm tra tính toàn vẹn dữ liệu (fail-fast): Không âm thầm embed chuỗi rỗng
        for idx, t in enumerate(texts):
            if not t or not isinstance(t, str) or not t.strip():
                raise ValueError(
                    f"Phát hiện văn bản rỗng hoặc không hợp lệ tại vị trí index {idx}. "
                    "Mọi Article bắt buộc phải có full_text hợp lệ trước khi sinh embedding."
                )

        embeddings = model.encode(
            texts,
            batch_size=bs,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embeddings

    def encode_query(self, query: str) -> List[float]:
        """
        Encode câu truy vấn (user query) thành vector đơn.
        
        Args:
            query: Chuỗi câu hỏi hoặc cụm từ tìm kiếm.
            
        Returns:
            List[float]: Vector embedding kích thước dimension đã được L2-normalized.
        """
        if not query or not isinstance(query, str) or not query.strip():
            raise ValueError("Query tìm kiếm không được để trống hoặc chỉ chứa khoảng trắng.")

        model = self.load_model()
        clean_query = query.strip()
        
        vec = model.encode(
            clean_query,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return vec.tolist()
