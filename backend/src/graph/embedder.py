"""
embedder.py
Module quản lý Embedding Model cho Legal Knowledge Graph.

Nhiệm vụ:
- Quản lý vòng đời của SentenceTransformer (mặc định darklethelong/vnlegal-lal)
- Ghép ngữ cảnh phả hệ vào text trước khi Embed (Context-Enriched Embedding)
- Encode danh sách passages (Article enriched text) sang dense vectors (1024-d)
- Encode user query sang dense vector phục vụ Semantic Vector Search
"""

import logging
import time
from typing import Any, Dict, List, Optional, Union

import numpy as np
import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer

from src.common.setting_config import get_settings

logger = logging.getLogger(__name__)


def build_enriched_text(
    article: Dict[str, Any], node_map: Dict[str, Dict[str, Any]]
) -> str:
    """
    Ghép nhãn ngữ cảnh phả hệ (Context-Enriched) vào trước nội dung điều luật:
    Định dạng: [Văn bản] [Phần] [Chương] [Mục] [Điều X: Tiêu đề]\n{full_text}
    """
    chain = []
    curr = article
    while curr and curr.get("parent_id"):
        pid = curr["parent_id"]
        curr = node_map.get(pid)
        if curr:
            chain.append(curr)
    chain.reverse()

    parts = []
    for c in chain:
        ctype = c.get("label") or c.get("type")
        title = (c.get("title") or "").strip()
        num = str(c.get("number") or "").strip()
        if ctype == "Document":
            parts.append(f"[{title}]")
        elif ctype == "Part":
            parts.append(f"[Phần {num}: {title}]" if title else f"[Phần {num}]")
        elif ctype == "Chapter":
            parts.append(f"[Chương {num}: {title}]" if title else f"[Chương {num}]")
        elif ctype == "Section":
            parts.append(f"[Mục {num}: {title}]" if title else f"[Mục {num}]")
        elif ctype == "SubSection":
            parts.append(f"[Tiểu mục {num}: {title}]" if title else f"[Tiểu mục {num}]")

    num_art = str(article.get("number") or "").strip()
    title_art = (article.get("title") or "").strip()
    if title_art and not title_art.lower().startswith("điều"):
        parts.append(f"[Điều {num_art}: {title_art}]")
    elif title_art:
        parts.append(f"[{title_art}]")
    else:
        parts.append(f"[Điều {num_art}]")

    header = " ".join(parts)
    full_text = (article.get("full_text") or article.get("text") or "").strip()
    return f"{header}\n{full_text}"


class NodeEmbedder:
    """
    Wrapper quản lý mô hình Embedding (mặc định darklethelong/vnlegal-lal).
    Hỗ trợ pipeline chuẩn của tác giả:
    - Maximum Sequence Length: 2048 tokens
    - Pooling: Last-token pooling (cho kiến trúc Decoder-only Qwen)
    - Query Prefix: Hướng dẫn truy xuất ngữ nghĩa cho câu hỏi
    """

    QUERY_PREFIX = "Instruct: Given a Vietnamese legal question, retrieve relevant legal passages that answer the question\nQuery: "

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        batch_size: Optional[int] = None,
        max_seq_length: int = 2048,
    ):
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model_name
        self.device = device or settings.embedding_device
        self.batch_size = (
            batch_size if batch_size is not None else settings.embedding_batch_size
        )
        self.max_seq_length = max_seq_length

        self.is_vnlegal = "vnlegal-lal" in self.model_name.lower()
        self._model = None
        self._tokenizer = None
        self._dimension: Optional[int] = None

    def load_model(self):
        """Khởi tạo và nạp model vào RAM/VRAM nếu chưa nạp."""
        if self._model is None:
            if self.device == "cpu":
                torch.set_num_threads(8)

            logger.info(
                "Đang nạp embedding model: %s (device=%s, max_seq_length=%d)...",
                self.model_name,
                self.device,
                self.max_seq_length,
            )
            start_time = time.time()

            if self.is_vnlegal:
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self._tokenizer.padding_side = "right"
                self._model = AutoModel.from_pretrained(self.model_name)
                self._model.to(self.device)
                self._model.eval()
                self._dimension = self._model.config.hidden_size
            else:
                self._model = SentenceTransformer(self.model_name, device=self.device)
                if hasattr(self._model, "max_seq_length"):
                    self._model.max_seq_length = self.max_seq_length
                if hasattr(self._model, "get_embedding_dimension"):
                    self._dimension = self._model.get_embedding_dimension()
                else:
                    self._dimension = self._model.get_sentence_embedding_dimension()

            elapsed = time.time() - start_time
            logger.info(
                "Model loaded thành công trong %.2fs (dimension=%d)",
                elapsed,
                self._dimension,
            )
        return self._model

    @property
    def dimension(self) -> int:
        """Kích thước vector embedding (1024 đối với VNLegal-LAL và BGE-M3)."""
        if self._dimension is None:
            self.load_model()
        return self._dimension

    @staticmethod
    def _last_token_pool(
        last_hidden_state: torch.Tensor, attention_mask: torch.Tensor
    ) -> torch.Tensor:
        """
        Trích xuất representation tại token thật cuối cùng, hỗ trợ cả right-padding và left-padding.
        """
        left_padding = attention_mask[:, -1].sum() == attention_mask.shape[0]
        if left_padding:
            return last_hidden_state[:, -1]
        sequence_lengths = attention_mask.sum(dim=1) - 1
        batch_size = last_hidden_state.shape[0]
        return last_hidden_state[
            torch.arange(batch_size, device=last_hidden_state.device), sequence_lengths
        ]

    def encode_passages(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        show_progress_bar: bool = True,
    ) -> np.ndarray:
        """
        Encode danh sách các đoạn văn bản (Article enriched text).
        Áp dụng last-token pooling và chuẩn hóa L2 theo chuẩn công bố của tác giả.
        """
        self.load_model()
        bs = batch_size or self.batch_size

        for idx, t in enumerate(texts):
            if not t or not isinstance(t, str) or not t.strip():
                raise ValueError(
                    f"Phát hiện văn bản rỗng hoặc không hợp lệ tại vị trí index {idx}. "
                    "Mọi Article bắt buộc phải có full_text hợp lệ trước khi sinh embedding."
                )

        if self.is_vnlegal:
            all_embs = []
            iterator = range(0, len(texts), bs)
            if show_progress_bar:
                iterator = tqdm(
                    iterator, desc=f"Embedding with {self.model_name} (2048 tokens)"
                )

            for i in iterator:
                batch = texts[i : i + bs]
                inputs = self._tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=self.max_seq_length,
                    return_tensors="pt",
                ).to(self.device)

                with torch.no_grad():
                    out = self._model(**inputs)

                # Last-token pooling chuẩn cho kiến trúc Decoder-only
                batch_embs = self._last_token_pool(
                    out.last_hidden_state, inputs["attention_mask"]
                )
                batch_embs = F.normalize(batch_embs, p=2, dim=1)
                all_embs.append(batch_embs.cpu().numpy())

            return np.vstack(all_embs)
        else:
            return self._model.encode(
                texts,
                batch_size=bs,
                show_progress_bar=show_progress_bar,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )

    def encode_query(self, query: str) -> List[float]:
        """
        Encode câu truy vấn (user query) thành vector đơn.
        Áp dụng QUERY_PREFIX cho mô hình retrieval bất đối xứng (asymmetric).
        """
        if not query or not isinstance(query, str) or not query.strip():
            raise ValueError(
                "Query tìm kiếm không được để trống hoặc chỉ chứa khoảng trắng."
            )

        self.load_model()
        clean_query = query.strip()

        if self.is_vnlegal:
            prompted_query = self.QUERY_PREFIX + clean_query
            inputs = self._tokenizer(
                [prompted_query],
                padding=True,
                truncation=True,
                max_length=self.max_seq_length,
                return_tensors="pt",
            ).to(self.device)

            with torch.no_grad():
                out = self._model(**inputs)

            embs = self._last_token_pool(
                out.last_hidden_state, inputs["attention_mask"]
            )
            embs = F.normalize(embs, p=2, dim=1)
            return embs.cpu().squeeze(0).tolist()
        else:
            vec = self._model.encode(
                clean_query,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
            return vec.tolist()
