"""
hybrid.py
Module tìm kiếm kết hợp Hybrid Search (Dense Semantic + BM25 Lexical) với Reciprocal Rank Fusion (RRF).

Nhiệm vụ:
- Triển khai BM25Okapi thuần cho ngữ liệu Điều luật (Article) pháp luật Việt Nam.
- Tiền xử lý văn bản tiếng Việt pháp lý (chuẩn hóa Unicode NFC, lowercase, tách âm tiết và bi-gram).
- Nạp ngữ liệu Article từ Neo4j (với cơ chế dự phòng từ data/processed/nodes.json).
- Hợp nhất kết quả từ SemanticSearcher và BM25Searcher qua thuật toán Reciprocal Rank Fusion (RRF).
- Khử trùng lặp theo định danh pháp lý (node_id) và bảo toàn Unified Data Contract cho Graph Traversal.
"""

from collections import Counter, defaultdict
import json
import math
import pathlib
import re
import sys
import time
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.graph.neo4j_client import Neo4jClient
from src.retrieval.semantic import SemanticSearcher
from src.utils.logger import setup_logger

logger = setup_logger("hybrid", "hybrid.log")

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_NODES_PATH = BACKEND_DIR / "data" / "processed" / "nodes.json"


def tokenize_vietnamese_legal(
    text: str, ngram_range: Tuple[int, int] = (1, 2)
) -> List[str]:
    """Tách từ/âm tiết và tạo n-gram cho văn bản pháp luật tiếng Việt.

    Hỗ trợ chuẩn hóa Unicode NFC, chuyển chữ thường và sinh unigram + bigram
    để bắt các thuật ngữ pháp lý ghép (ví dụ: 'bồi_thường', 'thiệt_hại', 'đặt_cọc').

    Args:
        text: Chuỗi văn bản cần tách từ.
        ngram_range: Khoảng n-gram cần sinh (mặc định (1, 2) cho unigram và bigram).

    Returns:
        Danh sách các token dạng chuỗi.
    """
    if not text or not isinstance(text, str):
        return []

    # 1. Chuẩn hóa Unicode NFC và chuyển chữ thường
    text = unicodedata.normalize("NFC", text.lower())

    # 2. Bóc tách các từ/âm tiết tiếng Việt và số hiệu điều khoản
    pattern = r"[a-z0-9àáâãèéêìíòóôõùúýăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]+"
    syllables = re.findall(pattern, text)
    if not syllables:
        return []

    tokens: List[str] = list(syllables)

    # 3. Sinh thêm bi-gram ghép các âm tiết liền kề
    if ngram_range[1] >= 2 and len(syllables) >= 2:
        bigrams = [
            f"{syllables[i]}_{syllables[i+1]}" for i in range(len(syllables) - 1)
        ]
        tokens.extend(bigrams)

    return tokens


class BM25Okapi:
    """Thuật toán BM25Okapi chuẩn, độc lập, tối ưu cho ngữ liệu văn bản pháp luật."""

    def __init__(
        self,
        corpus_tokens: List[List[str]],
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25,
    ):
        """Khởi tạo chỉ mục BM25 từ danh sách token của từng tài liệu trong corpus.

        Args:
            corpus_tokens: Danh sách các mảng token cho từng tài liệu.
            k1: Tham số điều chỉnh độ bão hòa tần số từ (mặc định 1.5).
            b: Tham số điều chỉnh mức độ phạt độ dài văn bản (mặc định 0.75).
            epsilon: Hệ số sàn cho IDF đối với các từ phổ biến cao.
        """
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.corpus_size = len(corpus_tokens)
        self.doc_lens = [len(doc) for doc in corpus_tokens]
        self.avgdl = (
            sum(self.doc_lens) / max(self.corpus_size, 1) if self.corpus_size > 0 else 0.0
        )

        # Tính tần số xuất hiện của từng từ trong tài liệu (TF) và trong cả tập (DF)
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        self.doc_term_freqs: List[Dict[str, int]] = []

        for doc in corpus_tokens:
            freqs = Counter(doc)
            self.doc_term_freqs.append(freqs)
            for term in freqs:
                self.doc_freqs[term] += 1

        # Tiền tính giá trị IDF cho toàn bộ từ điển
        self.idf: Dict[str, float] = {}
        negative_idfs = []
        for term, freq in self.doc_freqs.items():
            # Công thức Robertson-Spärck Jones có làm mịn tránh chia cho 0
            val = math.log(
                1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5)
            )
            self.idf[term] = val
            if val < 0:
                negative_idfs.append(term)

        # Xử lý các từ có IDF âm bằng giá trị epsilon * average_idf
        if self.idf:
            positive_idfs = [v for v in self.idf.values() if v > 0]
            avg_idf = (
                sum(positive_idfs) / len(positive_idfs) if positive_idfs else 0.0
            )
            eps = self.epsilon * avg_idf
            for term in negative_idfs:
                self.idf[term] = eps

    def get_scores(self, query_tokens: List[str]) -> List[float]:
        """Tính điểm BM25 cho toàn bộ các tài liệu trong tập ngữ liệu đối với truy vấn.

        Args:
            query_tokens: Danh sách token của câu truy vấn.

        Returns:
            Danh sách điểm BM25 tương ứng với từng tài liệu.
        """
        scores = [0.0] * self.corpus_size
        query_freqs = Counter(query_tokens)

        for term, qf in query_freqs.items():
            if term not in self.idf:
                continue
            idf_val = self.idf[term]

            for idx, doc_freqs in enumerate(self.doc_term_freqs):
                if term not in doc_freqs:
                    continue
                tf = doc_freqs[term]
                denom = tf + self.k1 * (
                    1.0 - self.b + self.b * (self.doc_lens[idx] / max(self.avgdl, 1e-6))
                )
                scores[idx] += idf_val * (tf * (self.k1 + 1.0)) / denom

        return scores


class BM25Searcher:
    """Dịch vụ tìm kiếm từ khóa (Lexical Search) trên tập Điều luật pháp luật."""

    def __init__(
        self,
        neo4j_client: Optional[Neo4jClient] = None,
        corpus_path: Optional[pathlib.Path] = None,
        k1: float = 1.5,
        b: float = 0.75,
    ):
        """Khởi tạo BM25Searcher và xây dựng chỉ mục BM25.

        Args:
            neo4j_client: Client Neo4j để nạp danh sách Điều luật.
            corpus_path: Đường dẫn file JSON dự phòng (mặc định nodes.json).
            k1: Tham số BM25 k1.
            b: Tham số BM25 b.
        """
        self.client = neo4j_client
        self.corpus_path = corpus_path or DEFAULT_NODES_PATH
        self.k1 = k1
        self.b = b

        self.articles: List[Dict[str, Any]] = []
        self.document_map: Dict[str, Dict[str, Any]] = {}
        self.bm25: Optional[BM25Okapi] = None

        self._load_corpus()

    def _load_corpus(self) -> None:
        """Nạp toàn bộ Article nodes và Document metadata để khởi tạo chỉ mục."""
        t0 = time.time()
        articles: List[Dict[str, Any]] = []
        document_map: Dict[str, Dict[str, Any]] = {}

        # 1. Ưu tiên đọc từ Neo4j nếu client có sẵn
        if self.client is not None:
            try:
                cypher_articles = """
                MATCH (n:Article)
                RETURN n.node_id AS node_id,
                       coalesce(n.label, 'Article') AS label,
                       n.number AS number,
                       n.title AS title,
                       n.full_text AS full_text,
                       n.document_id AS document_id,
                       n.parent_id AS parent_id
                ORDER BY n.node_id ASC
                """
                rows = self.client.execute_read(cypher_articles)
                if rows:
                    articles = rows
                    logger.info("Đã nạp %d Article nodes từ Neo4j cho BM25.", len(articles))

                cypher_docs = """
                MATCH (d:Document)
                RETURN d.node_id AS node_id,
                       coalesce(d.label, 'Document') AS label,
                       d.number AS number,
                       d.title AS title,
                       coalesce(d.full_text, d.text, '') AS full_text,
                       d.document_id AS document_id,
                       d.parent_id AS parent_id
                """
                doc_rows = self.client.execute_read(cypher_docs)
                for doc in doc_rows:
                    did = doc.get("document_id") or doc.get("node_id")
                    if did:
                        document_map[did] = doc
            except Exception as e:
                logger.warning("Không thể nạp dữ liệu từ Neo4j cho BM25: %s", e)

        # 2. Dự phòng: nạp từ file JSON nếu Neo4j không có dữ liệu
        if not articles and self.corpus_path.exists():
            try:
                with open(self.corpus_path, "r", encoding="utf-8") as f:
                    all_nodes = json.load(f)
                for item in all_nodes:
                    node_label = item.get("label") or item.get("type")
                    if node_label == "Article":
                        articles.append(
                            {
                                "node_id": item.get("node_id"),
                                "label": "Article",
                                "number": item.get("number"),
                                "title": item.get("title") or "",
                                "full_text": item.get("full_text") or item.get("text") or "",
                                "document_id": item.get("document_id"),
                                "parent_id": item.get("parent_id"),
                            }
                        )
                    elif node_label == "Document":
                        did = item.get("document_id") or item.get("node_id")
                        if did:
                            document_map[did] = {
                                "node_id": item.get("node_id") or did,
                                "label": "Document",
                                "number": item.get("number"),
                                "title": item.get("title") or "",
                                "full_text": item.get("full_text") or item.get("text") or "",
                                "document_id": did,
                                "parent_id": item.get("parent_id"),
                            }
                logger.info(
                    "Đã nạp %d Article nodes dự phòng từ %s cho BM25.",
                    len(articles),
                    self.corpus_path.name,
                )
            except Exception as e:
                logger.error("Lỗi đọc file nodes dự phòng: %s", e)

        self.articles = articles
        self.document_map = document_map

        if not self.articles:
            logger.warning("Corpus Article cho BM25 rỗng.")
            return

        # 3. Tiền xử lý token cho toàn bộ các Điều luật
        corpus_tokens = []
        for art in self.articles:
            doc_text = f"{art.get('title') or ''} {art.get('full_text') or ''}".strip()
            corpus_tokens.append(tokenize_vietnamese_legal(doc_text))

        self.bm25 = BM25Okapi(corpus_tokens, k1=self.k1, b=self.b)
        elapsed = (time.time() - t0) * 1000
        logger.info(
            "Xây dựng chỉ mục BM25 hoàn tất cho %d tài liệu (thời gian: %.2f ms).",
            len(self.articles),
            elapsed,
        )

    def search(
        self,
        query: str,
        top_k: int = 10,
        document_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Thực hiện tìm kiếm BM25 trên ngữ liệu Điều luật.

        Args:
            query: Câu truy vấn của người dùng.
            top_k: Số lượng kết quả cần trả về.
            document_filter: Bộ lọc theo document_id (nếu có).

        Returns:
            Dict chuẩn hóa tương thích với SemanticSearcher Unified Contract.
        """
        if not query or not query.strip() or self.bm25 is None or not self.articles:
            return {
                "query": query,
                "total_found": 0,
                "search_time_ms": 0.0,
                "model_name": "BM25Okapi",
                "results": [],
                "related_nodes": [],
                "related_documents": [],
            }

        t_start = time.time()
        query_tokens = tokenize_vietnamese_legal(query)
        scores = self.bm25.get_scores(query_tokens)

        # Ghép điểm và lọc theo document_filter
        scored_docs = []
        for idx, score in enumerate(scores):
            if score <= 0.0:
                continue
            art = self.articles[idx]
            if document_filter and art.get("document_id") != document_filter:
                continue
            scored_docs.append((score, art))

        # Sắp xếp điểm BM25 giảm dần
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_scored = scored_docs[:top_k]

        related_nodes: List[Dict[str, Any]] = []
        seen_doc_ids = set()
        related_documents: List[Dict[str, Any]] = []

        for rank, (score, art) in enumerate(top_scored, 1):
            related_nodes.append(
                {
                    "node_id": art.get("node_id"),
                    "label": art.get("label") or "Article",
                    "number": art.get("number"),
                    "title": art.get("title"),
                    "full_text": art.get("full_text"),
                    "document_id": art.get("document_id"),
                    "parent_id": art.get("parent_id"),
                    "rank": rank,
                    "score": round(float(score), 4),
                    "retrieval_source": "bm25",
                    "hop": 0,
                }
            )

            doc_id = art.get("document_id")
            if doc_id and doc_id not in seen_doc_ids:
                seen_doc_ids.add(doc_id)
                doc_node = self.document_map.get(doc_id)
                if doc_node:
                    related_documents.append(doc_node)
                else:
                    related_documents.append(
                        {
                            "node_id": doc_id,
                            "label": "Document",
                            "number": None,
                            "title": doc_id,
                            "full_text": "",
                            "document_id": doc_id,
                            "parent_id": None,
                        }
                    )

        total_time_ms = (time.time() - t_start) * 1000

        return {
            "query": query,
            "total_found": len(related_nodes),
            "search_time_ms": round(total_time_ms, 2),
            "model_name": "BM25Okapi",
            "results": related_nodes,
            "related_nodes": related_nodes,
            "related_documents": related_documents,
        }


def reciprocal_rank_fusion(
    semantic_nodes: List[Dict[str, Any]],
    bm25_nodes: List[Dict[str, Any]],
    k: int = 60,
    weight_semantic: float = 1.0,
    weight_bm25: float = 1.0,
) -> List[Dict[str, Any]]:
    """Hợp nhất danh sách node kết quả từ Semantic và BM25 theo chuẩn RRF.

    Công thức:
        RRF_Score(d) = weight_semantic / (k + rank_semantic(d))
                     + weight_bm25 / (k + rank_bm25(d))

    Khử trùng lặp tuyệt đối theo node_id.

    Args:
        semantic_nodes: Danh sách node từ Semantic Search (đã có rank, score).
        bm25_nodes: Danh sách node từ BM25 Search (đã có rank, score).
        k: Hằng số làm mịn rank (mặc định 60).
        weight_semantic: Trọng số cho điểm Semantic (mặc định 1.0).
        weight_bm25: Trọng số cho điểm BM25 (mặc định 1.0).

    Returns:
        Danh sách các node đã được hợp nhất, sắp xếp theo rrf_score giảm dần.
    """
    node_registry: Dict[str, Dict[str, Any]] = {}
    rrf_scores: Dict[str, float] = defaultdict(float)
    semantic_ranks: Dict[str, int] = {}
    semantic_raw_scores: Dict[str, float] = {}
    bm25_ranks: Dict[str, int] = {}
    bm25_raw_scores: Dict[str, float] = {}

    # 1. Ghi nhận điểm và thứ hạng Semantic
    for rank, node in enumerate(semantic_nodes, 1):
        nid = node.get("node_id")
        if not nid:
            continue
        node_registry[nid] = node
        semantic_ranks[nid] = rank
        semantic_raw_scores[nid] = node.get("score", 0.0)
        rrf_scores[nid] += weight_semantic / (k + rank)

    # 2. Ghi nhận điểm và thứ hạng BM25
    for rank, node in enumerate(bm25_nodes, 1):
        nid = node.get("node_id")
        if not nid:
            continue
        if nid not in node_registry:
            node_registry[nid] = node
        bm25_ranks[nid] = rank
        bm25_raw_scores[nid] = node.get("score", 0.0)
        rrf_scores[nid] += weight_bm25 / (k + rank)

    # 3. Tạo danh sách kết quả tổng hợp
    fused_list: List[Dict[str, Any]] = []
    for nid, base_node in node_registry.items():
        has_sem = nid in semantic_ranks
        has_bm = nid in bm25_ranks
        if has_sem and has_bm:
            source = "hybrid[semantic+bm25]"
        elif has_sem:
            source = "hybrid[semantic_only]"
        else:
            source = "hybrid[bm25_only]"

        combined = dict(base_node)
        score_val = rrf_scores[nid]
        combined["score"] = round(score_val, 6)
        combined["rrf_score"] = round(score_val, 6)
        combined["semantic_rank"] = semantic_ranks.get(nid)
        combined["semantic_score"] = semantic_raw_scores.get(nid)
        combined["bm25_rank"] = bm25_ranks.get(nid)
        combined["bm25_score"] = bm25_raw_scores.get(nid)
        combined["retrieval_source"] = source
        combined["hop"] = 0
        fused_list.append(combined)

    # 4. Sắp xếp theo điểm RRF giảm dần và gán lại rank 1-indexed
    fused_list.sort(key=lambda x: x["rrf_score"], reverse=True)
    for final_rank, item in enumerate(fused_list, 1):
        item["rank"] = final_rank

    return fused_list


class HybridSearcher:
    """Bộ tìm kiếm tích hợp Hybrid Search kết hợp Dense Semantic và Lexical BM25."""

    def __init__(
        self,
        semantic_searcher: SemanticSearcher,
        bm25_searcher: BM25Searcher,
        default_rrf_k: int = 60,
        weight_semantic: float = 1.0,
        weight_bm25: float = 1.0,
    ):
        """Khởi tạo HybridSearcher từ hai bộ tìm kiếm thành phần.

        Args:
            semantic_searcher: Thể hiện SemanticSearcher đã cấu hình vector store.
            bm25_searcher: Thể hiện BM25Searcher đã nạp corpus.
            default_rrf_k: Hằng số làm mịn RRF (mặc định 60).
            weight_semantic: Trọng số nhánh ngữ nghĩa.
            weight_bm25: Trọng số nhánh từ khóa.
        """
        self.semantic_searcher = semantic_searcher
        self.bm25_searcher = bm25_searcher
        self.rrf_k = default_rrf_k
        self.weight_semantic = weight_semantic
        self.weight_bm25 = weight_bm25

    def search(
        self,
        query: str,
        top_k: int = 10,
        document_filter: Optional[str] = None,
        candidate_multiplier: int = 3,
    ) -> Dict[str, Any]:
        """Thực hiện tìm kiếm Hybrid qua RRF và trả về kết quả chuẩn Unified Contract.

        Args:
            query: Nội dung câu hỏi truy vấn của người dùng.
            top_k: Số lượng kết quả cuối cùng cần lấy.
            document_filter: Tùy chọn lọc theo document_id (ví dụ 'BLDS_2015').
            candidate_multiplier: Hệ số nhân lấy ứng viên trước khi dung hợp (mặc định lấy top_k * 3 từ mỗi nhánh).

        Returns:
            Dict chuẩn hóa tương thích 100% với SemanticSearcher Unified Contract:
            {
                "query": str,
                "total_found": int,
                "search_time_ms": float,
                "semantic_time_ms": float,
                "bm25_time_ms": float,
                "fusion_method": "RRF",
                "results": [...],
                "related_nodes": [...],
                "related_documents": [...]
            }
        """
        if not query or not query.strip():
            return {
                "query": query,
                "total_found": 0,
                "search_time_ms": 0.0,
                "semantic_time_ms": 0.0,
                "bm25_time_ms": 0.0,
                "fusion_method": "RRF",
                "model_name": "HybridSearcher[Dense+BM25]",
                "results": [],
                "related_nodes": [],
                "related_documents": [],
            }

        t_start = time.time()
        fetch_k = max(top_k * candidate_multiplier, 20)

        # 1. Tìm kiếm bằng Semantic Vector
        t_sem = time.time()
        try:
            semantic_res = self.semantic_searcher.search(
                query=query, top_k=fetch_k, document_filter=document_filter
            )
        except Exception as e:
            logger.error("Lỗi khi chạy Semantic Search trong Hybrid: %s", e)
            semantic_res = {"related_nodes": [], "related_documents": []}
        semantic_time_ms = (time.time() - t_sem) * 1000

        # 2. Tìm kiếm bằng BM25 Lexical
        t_bm = time.time()
        try:
            bm25_res = self.bm25_searcher.search(
                query=query, top_k=fetch_k, document_filter=document_filter
            )
        except Exception as e:
            logger.error("Lỗi khi chạy BM25 Search trong Hybrid: %s", e)
            bm25_res = {"related_nodes": [], "related_documents": []}
        bm25_time_ms = (time.time() - t_bm) * 1000

        sem_nodes = semantic_res.get("related_nodes", [])
        bm_nodes = bm25_res.get("related_nodes", [])

        # 3. Hợp nhất bằng Reciprocal Rank Fusion (RRF)
        fused_nodes = reciprocal_rank_fusion(
            semantic_nodes=sem_nodes,
            bm25_nodes=bm_nodes,
            k=self.rrf_k,
            weight_semantic=self.weight_semantic,
            weight_bm25=self.weight_bm25,
        )

        final_nodes = fused_nodes[:top_k]

        # 4. Hợp nhất danh sách Document liên quan (khử trùng theo node_id)
        doc_registry: Dict[str, Dict[str, Any]] = {}
        for doc in semantic_res.get("related_documents", []):
            did = doc.get("node_id") or doc.get("document_id")
            if did:
                doc_registry[did] = doc

        for doc in bm25_res.get("related_documents", []):
            did = doc.get("node_id") or doc.get("document_id")
            if did and did not in doc_registry:
                doc_registry[did] = doc

        # Bổ sung các document tương ứng với các node trúng tuyển cuối cùng
        for n in final_nodes:
            did = n.get("document_id")
            if did and did not in doc_registry:
                doc_node = self.bm25_searcher.document_map.get(did)
                if doc_node:
                    doc_registry[did] = doc_node

        final_documents = list(doc_registry.values())
        total_time_ms = (time.time() - t_start) * 1000

        logger.info(
            "Hybrid Search hoàn tất: %d nodes dung hợp (Sem: %d, BM25: %d) trong %.2f ms.",
            len(final_nodes),
            len(sem_nodes),
            len(bm_nodes),
            total_time_ms,
        )

        return {
            "query": query,
            "total_found": len(final_nodes),
            "search_time_ms": round(total_time_ms, 2),
            "semantic_time_ms": round(semantic_time_ms, 2),
            "bm25_time_ms": round(bm25_time_ms, 2),
            "fusion_method": "RRF",
            "model_name": f"Hybrid[{self.semantic_searcher.embedder.model_name}+BM25]",
            "results": final_nodes,
            "related_nodes": final_nodes,
            "related_documents": final_documents,
        }
