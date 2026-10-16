"""
embed_nodes.py
Script pipeline sinh embedding cho Article nodes trong Neo4j bằng darklethelong/vnlegal-lal (kèm ghép Context-Enriched).

Quy trình:
1. Đọc tất cả Article nodes từ Neo4j hoặc nodes.json.
2. Ghép nhãn ngữ cảnh phả hệ [Văn bản > Phần > Chương > Mục > Điều] vào text trước khi Embed.
3. Sinh dense vector (1024-d) bằng darklethelong/vnlegal-lal (hoặc nạp từ cache an toàn).
4. Cache an toàn: phân tách file cache theo model và loại cấu hình (bảo toàn cache BGE-M3 cũ).
5. Ghi thuộc tính n.embedding vào từng Article node trên Neo4j theo batch.
6. Xác thực và kích hoạt Neo4j Vector Index (article_embeddings_idx) với timeout an toàn.
7. Đánh giá chất lượng Semantic Search với bộ benchmark định lượng: Hit@1, Hit@3, Hit@5, MRR.

Cách sử dụng:
    python scripts/embed_nodes.py --use-cache --test
    python scripts/embed_nodes.py --dry-run
    python scripts/embed_nodes.py --sample 10 --test
    python scripts/embed_nodes.py --index-only
"""

import datetime
import hashlib
import json
import math
import pathlib
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Hỗ trợ in tiếng Việt trên Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import numpy as np
from tqdm import tqdm

# Đảm bảo import được module từ src
BACKEND_DIR = pathlib.Path(__file__).resolve().parents[2]

from src.common.setting_config import get_settings
from src.graph.embedder import NodeEmbedder, build_enriched_text
from src.graph.neo4j_client import Neo4jClient
from src.utils.logger import setup_logger

logger = setup_logger(name="embed_nodes", filename="embed_nodes.log")

CACHE_DIR = BACKEND_DIR / "data" / "embeddings"
PROCESSED_NODES_FILE = BACKEND_DIR / "data" / "processed" / "nodes.json"
BENCHMARK_FILE = BACKEND_DIR / "data" / "eval" / "benchmark_queries.json"
INDEX_NAME = get_settings().vector_index_name


def get_cache_file(model_name: str, config_type: str = "enriched") -> pathlib.Path:
    """Tạo đường dẫn file cache riêng biệt theo tên model và dạng cấu hình."""
    slug = model_name.replace("/", "_")
    return CACHE_DIR / f"article_embeddings_{slug}_{config_type}.npz"


def load_benchmark_queries() -> List[Dict[str, Any]]:
    """Nạp bộ dữ liệu benchmark chuẩn 25 câu hỏi từ file benchmark_queries.json."""
    if BENCHMARK_FILE.exists():
        try:
            with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "queries" in data:
                return data["queries"]
            elif isinstance(data, list):
                return data
        except Exception as e:
            logger.warning(
                "Không thể nạp %s (%s). Sử dụng danh sách dự phòng.", BENCHMARK_FILE, e
            )

    return [
        {
            "query": "lãi suất cho vay theo thỏa thuận trong hợp đồng vay tài sản",
            "expected_ids": ["BLDS_2015_D468"],
            "topic": "Lãi suất thỏa thuận (Điều 468 BLDS)",
        },
        {
            "query": "bồi thường thiệt hại do tai nạn giao thông do nguồn nguy hiểm cao độ gây ra",
            "expected_ids": ["BLDS_2015_D601", "NQ_02_2022_D12"],
            "topic": "Nguồn nguy hiểm cao độ (Điều 601 BLDS / NQ 02/2022)",
        },
        {
            "query": "quyền và nghĩa vụ của bên nhận thế chấp tài sản",
            "expected_ids": ["BLDS_2015_D322", "BLDS_2015_D323"],
            "topic": "Bảo đảm thực hiện nghĩa vụ - Thế chấp tài sản (Điều 322, 323 BLDS)",
        },
        {
            "query": "hụi họ biêu phường chủ hụi bỏ trốn quỵt tiền và trách nhiệm của chủ họ",
            "expected_ids": ["BLDS_2015_D471", "ND_19_2019_D1", "ND_19_2019_D18"],
            "topic": "Hình thức giao dịch họ, hụi, biêu, phường",
        },
        {
            "query": "thực hiện hợp đồng vay tài sản không kỳ hạn và không có lãi",
            "expected_ids": ["BLDS_2015_D469", "BLDS_2015_D470", "BLDS_2015_D463"],
            "topic": "Hợp đồng vay không kỳ hạn / không lãi",
        },
    ]


def compute_ndcg_at_k(actual_ranks: List[int], num_relevant: int, k: int = 5) -> float:
    """Tính NDCG@k theo binary relevance cho truy vấn có thể có nhiều expected_ids.

    Args:
        actual_ranks: Danh sách thứ hạng (1-indexed) của các kết quả đúng xuất hiện trong top-k.
        num_relevant: Tổng số tài liệu liên quan kỳ vọng (|expected_ids|).
        k: Ngưỡng cắt rank (mặc định 5).
    """
    if num_relevant <= 0:
        return 0.0
    dcg = sum(1.0 / math.log2(r + 1) for r in actual_ranks if r <= k)
    ideal_count = min(num_relevant, k)
    idcg = sum(1.0 / math.log2(r + 1) for r in range(1, ideal_count + 1))
    return dcg / idcg if idcg > 0 else 0.0


def compute_corpus_hash(node_ids: List[str], texts: List[str]) -> str:
    """Tính mã băm SHA256 đại diện cho toàn bộ nội dung ngữ liệu (Corpus Hash)."""
    hasher = hashlib.sha256()
    for nid, txt in zip(node_ids, texts):
        hasher.update(nid.encode("utf-8"))
        hasher.update(b":")
        hasher.update(txt.encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()


def fetch_articles(client: Optional[Neo4jClient] = None) -> List[Dict[str, Any]]:
    """Truy vấn toàn bộ Article nodes từ Neo4j, tự động fallback sang nodes.json nếu Neo4j chưa online."""
    if client:
        try:
            query = """
            MATCH (n:Article)
            RETURN n.node_id AS node_id,
                   n.number AS number,
                   n.title AS title,
                   n.full_text AS full_text,
                   n.parent_id AS parent_id,
                   n.document_id AS document_id
            ORDER BY n.node_id
            """
            results = client.execute_read(query)
            if results:
                logger.info("Đã lấy %d Article nodes từ Neo4j.", len(results))
                return results
        except Exception as e:
            logger.warning(
                "Chưa thể kết nối Neo4j (%s). Tự động fallback sang đọc từ nodes.json...",
                e,
            )

    if PROCESSED_NODES_FILE.exists():
        import json

        with open(PROCESSED_NODES_FILE, "r", encoding="utf-8") as f:
            all_nodes = json.load(f)
        articles = [
            n for n in all_nodes
            if (n.get("label") or n.get("type")) == "Article"
        ]
        articles.sort(key=lambda x: x["node_id"])
        logger.info("Đã lấy %d Article nodes từ file nodes.json.", len(articles))
        return articles

    return []


def save_embeddings_cache(
    file_path: pathlib.Path,
    node_ids: List[str],
    vectors: np.ndarray,
    model_name: str,
    dimension: int,
    corpus_hash: str,
) -> None:
    """Lưu embedding vào file nén .npz kèm đầy đủ metadata bảo vệ."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        file_path,
        node_ids=np.array(node_ids),
        vectors=vectors,
        model_name=np.array([model_name]),
        dimension=np.array([dimension]),
        corpus_hash=np.array([corpus_hash]),
        created_at=np.array([datetime.datetime.now().isoformat()]),
    )
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    logger.info(
        "Đã lưu cache embedding tại %s (%.2f MB, hash=%s)",
        file_path,
        file_size_mb,
        corpus_hash,
    )
    print(f">> [CACHE] Đã lưu cache embedding vào: {file_path} ({file_size_mb:.2f} MB)")


def load_embeddings_cache(
    file_path: pathlib.Path,
    expected_node_ids: List[str],
    expected_model: str,
    expected_dim: int,
    expected_corpus_hash: str,
) -> Optional[Tuple[List[str], np.ndarray]]:
    """
    Nạp embedding từ file nén .npz với xác thực nghiêm ngặt 4 lớp:
    1. Danh sách node_id
    2. Tên model embedding
    3. Số chiều vector (dimension)
    4. Mã hash nội dung văn bản (corpus_hash)
    """
    if not file_path.exists():
        return None

    try:
        data = np.load(file_path, allow_pickle=False)
    except Exception as e:
        logger.warning("Không thể đọc cache file %s: %s", file_path, e)
        print(f"[CACHE ERROR] Lỗi khi đọc file cache: {e}")
        return None

    cached_ids = data["node_ids"].tolist() if "node_ids" in data else []
    cached_model = str(data["model_name"][0]) if "model_name" in data else "unknown"
    cached_dim = (
        int(data["dimension"][0])
        if "dimension" in data
        else (data["vectors"].shape[1] if "vectors" in data else 0)
    )
    cached_hash = str(data["corpus_hash"][0]) if "corpus_hash" in data else None

    # 1. Kiểm tra danh sách node_id
    if cached_ids != expected_node_ids:
        logger.warning(
            "Cache từ chối: Danh sách node_id không khớp (%d vs %d)",
            len(cached_ids),
            len(expected_node_ids),
        )
        print(
            f"[CACHE WARN] Từ chối cache: Danh sách node_id không khớp với database ({len(cached_ids)} vs {len(expected_node_ids)})."
        )
        return None

    # 2. Kiểm tra model_name
    if cached_model != expected_model:
        logger.warning(
            "Cache từ chối: Model mismatch (cached=%s, expected=%s)",
            cached_model,
            expected_model,
        )
        print(
            f"[CACHE WARN] Từ chối cache: Model không khớp (Cache: '{cached_model}' != Hiện tại: '{expected_model}')."
        )
        return None

    # 3. Kiểm tra dimension
    if cached_dim != expected_dim:
        logger.warning(
            "Cache từ chối: Dimension mismatch (cached=%d, expected=%d)",
            cached_dim,
            expected_dim,
        )
        print(
            f"[CACHE WARN] Từ chối cache: Dimension không khớp (Cache: {cached_dim} != Hiện tại: {expected_dim})."
        )
        return None

    # 4. Kiểm tra corpus hash
    if cached_hash != expected_corpus_hash:
        logger.warning(
            "Cache từ chối: Corpus hash mismatch (cached=%s, current=%s)",
            cached_hash,
            expected_corpus_hash,
        )
        print(
            "[CACHE WARN] Từ chối cache: Nội dung văn bản (full_text) đã bị thay đổi so với lúc tạo cache."
        )
        return None

    vectors = data["vectors"]
    if (
        vectors.shape != (len(expected_node_ids), expected_dim)
        or not np.isfinite(vectors).all()
    ):
        raise ValueError("Cache vectors sai shape hoặc NaN/Inf.")
    created_at = str(data["created_at"][0]) if "created_at" in data else "unknown"
    logger.info(
        "Nạp cache hợp lệ thành công từ %s (model=%s, dim=%d, hash=%s)",
        file_path,
        cached_model,
        cached_dim,
        cached_hash,
    )
    print(
        f">> [CACHE] Nạp thành công {len(cached_ids):,} vector từ cache hợp lệ: {file_path}"
    )
    print(
        f"   Model: {cached_model} | Dim: {cached_dim} | Hash: {cached_hash[:12]}... | Tạo lúc: {created_at}"
    )
    return cached_ids, vectors


def update_neo4j_embeddings(
    client: Neo4jClient,
    node_ids: List[str],
    vectors: np.ndarray,
    batch_size: int = 150,
) -> None:
    """Cập nhật thuộc tính embedding vào từng Article node trên Neo4j theo batch."""
    print(
        f"\n>> [NEO4J] Đang ghi {len(node_ids):,} vector vào database (batch size = {batch_size})..."
    )
    logger.info("Bắt đầu cập nhật embedding vào Neo4j cho %d nodes", len(node_ids))

    total = len(node_ids)
    cypher_query = """
    UNWIND $batch AS item
    MATCH (n:Article {node_id: item.node_id})
    SET n.embedding = item.embedding
    """

    with tqdm(total=total, desc="Ghi vào Neo4j", unit="node") as pbar:
        for i in range(0, total, batch_size):
            chunk_ids = node_ids[i : i + batch_size]
            chunk_vecs = vectors[i : i + batch_size].tolist()
            batch_data = [
                {"node_id": nid, "embedding": vec}
                for nid, vec in zip(chunk_ids, chunk_vecs)
            ]
            client.execute_write(cypher_query, {"batch": batch_data})
            pbar.update(len(batch_data))

    logger.info("Đã hoàn tất cập nhật embedding vào Neo4j.")
    print(">> [NEO4J] Cập nhật embedding thành công!")


def ensure_vector_index(
    client: Neo4jClient, dimension: int, timeout_seconds: int = 60
) -> None:
    """
    Kiểm tra và đảm bảo Vector Index tồn tại, đúng cấu hình dimension & similarity function.
    Nếu index cũ sai cấu hình thì dừng, giữ nguyên để rollback.
    Chờ index chuyển sang trạng thái ONLINE (raise RuntimeError nếu quá thời gian timeout).
    """
    print(
        f"\n>> [INDEX] Đang kiểm tra cấu hình Vector Index '{INDEX_NAME}' (dim={dimension}, similarity='cosine')..."
    )

    check_query = f"""
    SHOW VECTOR INDEXES YIELD name, state, populationPercent, options
    WHERE name = '{INDEX_NAME}'
    RETURN name, state, populationPercent, options
    """
    existing = client.execute_read(check_query)
    need_create = True

    if existing:
        idx_info = existing[0]
        options = idx_info.get("options") or {}
        index_config = options.get("indexConfig") or {}
        curr_dim = index_config.get("vector.dimensions")
        curr_sim = (index_config.get("vector.similarity_function") or "").lower()

        # Kiểm tra xem cấu hình index có khớp hay không
        if curr_dim == dimension and curr_sim == "cosine":
            logger.info(
                "Vector Index %s đã tồn tại và khớp cấu hình (dim=%d, sim=%s).",
                INDEX_NAME,
                curr_dim,
                curr_sim,
            )
            print(
                f">> [INDEX] Index '{INDEX_NAME}' đã tồn tại và khớp cấu hình (dim={curr_dim}, sim={curr_sim})."
            )
            need_create = False
        else:
            logger.warning(
                "Vector Index %s cấu hình không khớp (dim: %s vs %s, sim: %s vs cosine). Giữ nguyên index và dừng migration.",
                INDEX_NAME,
                curr_dim,
                dimension,
                curr_sim,
            )
            print(
                f"[INDEX WARN] Index '{INDEX_NAME}' không khớp cấu hình (dim={curr_dim} vs {dimension}). Giữ nguyên index và dừng migration."
            )
            raise ValueError("Index Neo4j khác cấu hình; giữ nguyên để rollback.")
            need_create = True

    if need_create:
        create_index_cypher = f"""
        CREATE VECTOR INDEX {INDEX_NAME}
        FOR (n:Article) ON (n.embedding)
        OPTIONS {{indexConfig: {{
            `vector.dimensions`: {dimension},
            `vector.similarity_function`: 'cosine'
        }}}}
        """
        client.execute_write(create_index_cypher)
        logger.info("Đã gửi lệnh tạo Vector Index %s", INDEX_NAME)
        print(f">> [INDEX] Đã gửi lệnh tạo Vector Index '{INDEX_NAME}'.")

    # Chờ index đạt trạng thái ONLINE
    print(
        f">> [INDEX] Đang chờ index '{INDEX_NAME}' chuyển sang trạng thái ONLINE (timeout={timeout_seconds}s)..."
    )
    start_wait = time.time()
    last_state = "UNKNOWN"
    last_pop = 0.0

    while time.time() - start_wait < timeout_seconds:
        records = client.execute_read(check_query)
        if records:
            last_state = records[0].get("state", "UNKNOWN")
            last_pop = records[0].get("populationPercent", 0.0)
            if last_state == "ONLINE":
                print(
                    f">> [INDEX] Index '{INDEX_NAME}' đã sẵn sàng (State: ONLINE, Populated: {last_pop}%)."
                )
                logger.info(
                    "Vector Index %s ONLINE (Populated: %s%%)", INDEX_NAME, last_pop
                )
                return
            elif last_state == "FAILED":
                raise RuntimeError(
                    f"Vector Index '{INDEX_NAME}' bị FAILED trong quá trình index trên Neo4j."
                )
        time.sleep(1)

    raise RuntimeError(
        f"Timeout ({timeout_seconds}s): Vector Index '{INDEX_NAME}' chưa chuyển sang ONLINE. "
        f"Trạng thái hiện tại: {last_state} (Populated: {last_pop}%)."
    )


def run_retrieval_benchmark(
    client: Neo4jClient, embedder: NodeEmbedder, top_k: int = 5
) -> Dict[str, float]:
    """
    Chạy bộ đánh giá định lượng (Benchmark) Retrieval:
    Tính toán Hit@1, Hit@3, Hit@5, MRR và NDCG@5 phục vụ báo cáo khoa học.
    """
    benchmark_queries = load_benchmark_queries()
    total_queries = len(benchmark_queries)

    print("\n" + "=" * 90)
    print(
        f"       BÁO CÁO ĐÁNH GIÁ ĐỊNH LƯỢNG RETRIEVAL ({total_queries} CÂU HỎI BENCHMARK)"
    )
    print("=" * 90)

    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0
    rr_scores: List[float] = []
    ndcg_scores: List[float] = []
    latencies: List[float] = []

    search_cypher = f"""
    CALL db.index.vector.queryNodes('{INDEX_NAME}', $top_k, $query_vector)
    YIELD node, score
    RETURN node.node_id AS node_id,
           node.title AS title,
           node.full_text AS full_text,
           score
    ORDER BY score DESC
    """

    for idx, test_case in enumerate(benchmark_queries, 1):
        query = test_case["query"]
        expected_ids = set(test_case["expected_ids"])
        topic = test_case.get("topic", "")

        # Encode query
        t0 = time.time()
        q_vec = embedder.encode_query(query)
        encode_time = (time.time() - t0) * 1000

        # Query Neo4j Vector Index
        t1 = time.time()
        results = client.execute_read(
            search_cypher, {"top_k": top_k, "query_vector": q_vec}
        )
        search_time = (time.time() - t1) * 1000
        total_time = encode_time + search_time
        latencies.append(total_time)

        # Danh sách rank của tất cả các kết quả đúng trong top_k
        hit_ranks = [
            rank
            for rank, res in enumerate(results, 1)
            if res["node_id"] in expected_ids
        ]
        first_hit_rank: Optional[int] = hit_ranks[0] if hit_ranks else None

        # Cập nhật metrics
        is_hit_1 = 1 if (first_hit_rank == 1) else 0
        is_hit_3 = 1 if (first_hit_rank is not None and first_hit_rank <= 3) else 0
        is_hit_5 = 1 if (first_hit_rank is not None and first_hit_rank <= 5) else 0
        rr = (1.0 / first_hit_rank) if first_hit_rank is not None else 0.0
        ndcg = compute_ndcg_at_k(hit_ranks, num_relevant=len(expected_ids), k=5)

        hits_at_1 += is_hit_1
        hits_at_3 += is_hit_3
        hits_at_5 += is_hit_5
        rr_scores.append(rr)
        ndcg_scores.append(ndcg)

        status_icon = "[PASS]" if is_hit_1 else ("[TOP5]" if is_hit_5 else "[FAIL]")
        rank_str = f"Rank #{first_hit_rank}" if first_hit_rank else "NOT FOUND"

        print(f"\n[Test {idx:02d}/{total_queries}] {status_icon} Chủ đề: {topic}")
        print(f'  Query: "{query}"')
        print(
            f"  Kỳ vọng: {sorted(list(expected_ids))} -> Kết quả: {rank_str} (RR = {rr:.2f}, NDCG@5 = {ndcg:.2f})"
        )
        print(
            f"  Thời gian: Encode {encode_time:.1f}ms | Search {search_time:.1f}ms | Tổng {total_time:.1f}ms"
        )

        for rank, res in enumerate(results, 1):
            nid = res["node_id"]
            score = res["score"]
            title = res.get("title") or ""
            mark = "[HIT]   " if nid in expected_ids else "        "
            print(f"    {mark} Top {rank} [{score:.4f}] {nid} — {title}")

    # Tổng hợp chỉ số
    hit_at_1_rate = hits_at_1 / total_queries
    hit_at_3_rate = hits_at_3 / total_queries
    hit_at_5_rate = hits_at_5 / total_queries
    mrr = sum(rr_scores) / total_queries
    ndcg_at_5 = sum(ndcg_scores) / total_queries
    avg_latency = sum(latencies) / total_queries

    print("\n" + "-" * 90)
    print("                        TỔNG HỢP CHỈ SỐ ĐỊNH LƯỢNG")
    print("-" * 90)
    print(f"  • Số lượng câu hỏi đánh giá : {total_queries}")
    print(
        f"  • Hit@1 (Đúng ở vị trí Top 1): {hits_at_1}/{total_queries} ({hit_at_1_rate * 100:.1f}%)"
    )
    print(
        f"  • Hit@3 (Xuất hiện trong Top 3): {hits_at_3}/{total_queries} ({hit_at_3_rate * 100:.1f}%)"
    )
    print(
        f"  • Hit@5 (Xuất hiện trong Top 5): {hits_at_5}/{total_queries} ({hit_at_5_rate * 100:.1f}%)"
    )
    print(f"  • MRR (Mean Reciprocal Rank) : {mrr:.4f}")
    print(f"  • NDCG@5                     : {ndcg_at_5:.4f}")
    print(f"  • Độ trễ trung bình mỗi câu  : {avg_latency:.1f} ms")
    print("=" * 90 + "\n")

    return {
        "Hit@1": hit_at_1_rate,
        "Hit@3": hit_at_3_rate,
        "Hit@5": hit_at_5_rate,
        "MRR": mrr,
        "NDCG@5": ndcg_at_5,
        "Avg_Latency_ms": avg_latency,
    }


def run_embedding_pipeline(args, client, embedder, store_factory):
    """Chạy migration với các dependency được composition root cung cấp."""

    if args.sample is not None and args.sample < 1:
        raise ValueError("--sample phải lớn hơn 0.")
    if args.dry_run and args.index_only:
        raise ValueError("Không kết hợp --dry-run và --index-only.")
    if args.test and args.store == "chroma":
        raise ValueError("Dùng scripts.check_chroma_migration để benchmark Chroma.")
    try:
        # 1. Lấy dữ liệu Article từ Neo4j
        print(">> [BƯỚC 1] Đọc corpus Article...")
        articles = fetch_articles(client)
        if not articles:
            print("[ERROR] Không tìm thấy node Article nào trong Neo4j!")
            return

        print(f">> [BƯỚC 1] Đã tìm thấy {len(articles):,} Article nodes.")

        # Fail-fast: Kiểm tra Article không có full_text
        for a in articles:
            text = a.get("full_text")
            if not text or not isinstance(text, str) or not text.strip():
                raise ValueError(
                    f"Dữ liệu lỗi: Node Article '{a['node_id']}' không có full_text hoặc nội dung rỗng. "
                    "Vui lòng kiểm tra khâu tiền xử lý dữ liệu trước khi sinh embedding."
                )

        # Chế độ --index-only: chỉ kiểm tra hoặc tạo lại index
        if args.index_only:
            if args.store == "chroma":
                raise ValueError("--index-only chỉ áp dụng cho Neo4j.")
            ensure_vector_index(client, embedder.dimension)
            if args.test:
                run_retrieval_benchmark(client, embedder)
            return

        # Nạp bản đồ phân cấp để ghép ngữ cảnh phả hệ
        node_map = {}
        if PROCESSED_NODES_FILE.exists():
            import json

            with open(PROCESSED_NODES_FILE, "r", encoding="utf-8") as f:
                all_nodes = json.load(f)
                node_map = {n["node_id"]: n for n in all_nodes}

        # Chế độ --dry-run: Tuyệt đối KHÔNG ghi vào database, KHÔNG tạo index
        if args.dry_run:
            sample_n = 5
            print(f"\n>> [DRY-RUN] Chế độ chạy thử nghiệm an toàn:")
            print(f"   - Tuyệt đối KHÔNG ghi dữ liệu vào Neo4j.")
            print(f"   - Tuyệt đối KHÔNG tạo/sửa đổi Vector Index.")
            dry_samples = articles[:sample_n]
            dry_texts = [
                build_enriched_text(a, node_map) if node_map else a["full_text"]
                for a in dry_samples
            ]
            print(
                f">> [DRY-RUN] Mẫu text có ngữ cảnh phả hệ:\n{dry_texts[0][:250]}...\n"
            )
            print(
                f">> [DRY-RUN] Đang encode thử {sample_n} articles bằng model '{embedder.model_name}'..."
            )
            t0 = time.time()
            sample_vecs = embedder.encode_passages(dry_texts, show_progress_bar=False)
            t_sample = time.time() - t0
            print(f">> [DRY-RUN] Encode thành công {sample_vecs.shape[0]} mẫu:")
            print(
                f"   Shape: {sample_vecs.shape} | Dim: {sample_vecs.shape[1]} | Thời gian: {t_sample:.2f}s ({t_sample/sample_n:.2f}s/mẫu)"
            )
            print(
                ">> [DRY-RUN] Hoàn tất kiểm tra an toàn. Cơ sở dữ liệu nguyên vẹn 100%.\n"
            )
            return

        # Chế độ --sample N: Cắt tập con nếu người dùng yêu cầu
        if args.sample:
            print(f">> [SAMPLE] Giới hạn xử lý {args.sample} Article nodes đầu tiên...")
            articles = articles[: args.sample]

        node_ids = [a["node_id"] for a in articles]
        # Ghép ngữ cảnh phả hệ vào text trước khi Embed
        texts = [
            build_enriched_text(a, node_map) if node_map else a["full_text"]
            for a in articles
        ]

        # 2. Tính mã băm ngữ liệu (Corpus Hash)
        corpus_hash = compute_corpus_hash(node_ids, texts)
        logger.info("Corpus SHA256: %s (cho %d articles)", corpus_hash, len(node_ids))

        target_cache_file = get_cache_file(embedder.model_name, "enriched")

        vectors = None
        # 3. Xử lý Embedding: Kiểm tra Cache an toàn 4 lớp (bảo toàn cache cũ)
        if target_cache_file.exists() and not args.sample:
            cached_data = load_embeddings_cache(
                target_cache_file,
                expected_node_ids=node_ids,
                expected_model=embedder.model_name,
                expected_dim=embedder.dimension,
                expected_corpus_hash=corpus_hash,
            )
            if cached_data is not None:
                _, vectors = cached_data

        if vectors is None:
            print(
                f"\n>> [BƯỚC 2] Bắt đầu sinh embedding (Context-Enriched) cho {len(texts):,} articles bằng model '{embedder.model_name}'..."
            )
            print(
                f">> Cấu hình: Device={embedder.device}, Batch Size={embedder.batch_size}"
            )
            t_start = time.time()

            vectors = embedder.encode_passages(texts, show_progress_bar=True)

            elapsed = time.time() - t_start
            dim = vectors.shape[1]
            print(
                f">> [BƯỚC 2] Hoàn tất sinh embedding: {vectors.shape[0]:,} vectors, dim={dim}, tổng thời gian={elapsed:.1f}s ({elapsed/len(texts):.2f}s/bài)"
            )

            # Lưu cache an toàn (chỉ khi không dùng --sample)
            if not args.sample:
                print(
                    f"\n>> [BƯỚC 3] Lưu kết quả embedding vào cache riêng biệt: {target_cache_file.name}..."
                )
                save_embeddings_cache(
                    target_cache_file,
                    node_ids=node_ids,
                    vectors=vectors,
                    model_name=embedder.model_name,
                    dimension=dim,
                    corpus_hash=corpus_hash,
                )

        # 4. Ghi vào Neo4j
        print(f"\n>> [BƯỚC 4] Ghi embedding: {args.store}...")
        if args.store in ("chroma", "dual"):
            store = store_factory(embedder.model_name, vectors.shape[1])
            try:
                metadata = [
                    dict(
                        node_id=a["node_id"],
                        label="Article",
                        document_id=a["document_id"],
                        number=str(a["number"]),
                        title=a.get("title") or "",
                    )
                    for a in articles
                ]
                existing = store.collection.metadata or {}
                if existing.get("corpus_hash") not in (None, corpus_hash):
                    raise ValueError(
                        "Collection khác corpus; dùng collection mới để migration an toàn."
                    )
                stored_ids = set(store.get()["ids"])
                if stored_ids - set(node_ids):
                    raise ValueError("Collection có node ngoài corpus; không tự xóa.")
                store.upsert(node_ids, vectors, texts, metadata)
                store.collection.modify(
                    metadata={**existing, "corpus_hash": corpus_hash}
                )
                print(f"Chroma: {store.count()} records")
            finally:
                store.close()
        if args.store in ("neo4j", "dual"):
            ensure_vector_index(client, vectors.shape[1])
            update_neo4j_embeddings(client, node_ids, vectors)

        # 6. Benchmark Evaluation
        if args.test and client is not None:
            print("\n>> [BƯỚC 6] Khởi chạy bộ đánh giá Retrieval Benchmark...")
            run_retrieval_benchmark(client, embedder, top_k=5)

        print("\n=== HOÀN THÀNH TOÀN BỘ TIẾN TRÌNH EMBEDDING CHO LEGAL GRAPH ===\n")

    finally:
        if client is not None:
            client.close()
