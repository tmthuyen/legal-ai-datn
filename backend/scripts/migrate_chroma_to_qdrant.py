"""Script di chuyển (migrate) dữ liệu vector từ ChromaDB và NPZ Cache sang Qdrant."""

import hashlib
import json
import pathlib
import sys
import time

# Đảm bảo import được module từ backend (src)
BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import numpy as np

from src.common.setting_config import get_settings
from src.graph.embedder import NodeEmbedder, build_enriched_text
from src.vector.chroma_store import ChromaVectorStore
from src.vector.qdrant_store import QdrantVectorStore

DATA_DIR = BACKEND_DIR / "data"
NODES_FILE = DATA_DIR / "processed" / "nodes.json"
CACHE_DIR = DATA_DIR / "embeddings"


def compute_corpus_hash(articles):
    """Tính hash SHA-256 trên toàn bộ Article ID và nội dung full_text."""
    hasher = hashlib.sha256()
    for a in sorted(articles, key=lambda x: x["node_id"]):
        hasher.update(a["node_id"].encode("utf-8"))
        hasher.update((a.get("full_text") or "").encode("utf-8"))
    return hasher.hexdigest()


def main():
    print("=" * 70)
    print("   CHUYỂN ĐỔI (MIGRATE) VECTOR STORE: CHROMADB -> QDRANT")
    print("=" * 70)

    settings = get_settings()
    dimension = 1024
    model_name = settings.embedding_model_name
    qdrant_location = settings.qdrant_url or (BACKEND_DIR / settings.qdrant_path)
    collection_name = settings.qdrant_collection

    print(f">> Model: {model_name} (Dimension: {dimension})")
    print(f">> Qdrant location: {qdrant_location}")
    print(f">> Qdrant collection: {collection_name}")

    # 1. Đọc Article nodes từ nodes.json
    print("\n>> [BƯỚC 1] Đọc Article nodes từ nodes.json...")
    if not NODES_FILE.exists():
        print(f"[ERROR] Không tìm thấy file {NODES_FILE}")
        sys.exit(1)

    with open(NODES_FILE, "r", encoding="utf-8") as f:
        all_nodes = json.load(f)

    node_map = {n["node_id"]: n for n in all_nodes}
    articles = [n for n in all_nodes if n.get("label") == "Article"]
    print(f">> Tìm thấy {len(articles):,} Article nodes trong nodes.json.")

    corpus_hash = compute_corpus_hash(articles)
    print(f">> Corpus hash: {corpus_hash[:16]}...")

    # 2. Thu thập vector hiện có từ ChromaDB hoặc NPZ cache
    print("\n>> [BƯỚC 2] Thu thập vectors từ ChromaDB / NPZ Cache...")
    existing_vectors = {}  # node_id -> vector
    existing_texts = {}    # node_id -> enriched_text

    # Thử từ ChromaDB
    chroma_path = BACKEND_DIR / settings.chroma_path
    if chroma_path.exists():
        try:
            ch_store = ChromaVectorStore(
                path=chroma_path,
                collection_name=settings.chroma_collection,
                model_name=model_name,
                dimension=dimension,
                create=False,
            )
            ch_data = ch_store.get()
            ch_ids = ch_data.get("ids", [])
            ch_vecs = ch_data.get("embeddings", [])
            ch_docs = ch_data.get("documents", [])
            for nid, vec, doc in zip(ch_ids, ch_vecs, ch_docs):
                if vec is not None and len(vec) == dimension:
                    existing_vectors[nid] = np.array(vec, dtype=np.float32)
                    existing_texts[nid] = doc
            ch_store.close()
            print(f">> Đã đọc được {len(existing_vectors):,} vectors từ ChromaDB.")
        except Exception as e:
            print(f">> Lưu ý: Không mở được ChromaDB ({e}). Sẽ đọc từ NPZ Cache.")

    # Thử từ NPZ cache nếu còn thiếu
    slug = model_name.replace("/", "_")
    npz_path = CACHE_DIR / f"article_embeddings_{slug}_enriched.npz"
    if npz_path.exists():
        try:
            data = np.load(npz_path, allow_pickle=True)
            npz_ids = data["node_ids"]
            npz_vecs = data["vectors"]
            loaded_from_npz = 0
            for nid, vec in zip(npz_ids, npz_vecs):
                if nid not in existing_vectors and len(vec) == dimension:
                    existing_vectors[str(nid)] = np.array(vec, dtype=np.float32)
                    loaded_from_npz += 1
            if loaded_from_npz > 0:
                print(f">> Bổ sung thêm {loaded_from_npz:,} vectors từ NPZ cache.")
        except Exception as e:
            print(f">> Lỗi đọc NPZ cache: {e}")

    # 3. Kiểm tra xem còn Article nào chưa có vector không (ví dụ: HNGĐ)
    missing_articles = [a for a in articles if a["node_id"] not in existing_vectors]
    if missing_articles:
        print(f"\n>> [BƯỚC 3] Phát hiện {len(missing_articles):,} Article nodes chưa có vector (cần encode)...")
        print(">> Đang tải mô hình embedding để sinh vector bổ sung...")
        embedder = NodeEmbedder(model_name=model_name)
        embedder.load_model()

        missing_texts = [build_enriched_text(a, node_map) for a in missing_articles]
        print(f">> Đang encode {len(missing_articles)} articles...")
        new_vectors = embedder.encode_passages(missing_texts)

        for a, text, vec in zip(missing_articles, missing_texts, new_vectors):
            nid = a["node_id"]
            existing_vectors[nid] = vec
            existing_texts[nid] = text
        print(f">> Encode thành công {len(missing_articles)} articles bổ sung!")
    else:
        print("\n>> [BƯỚC 3] Tất cả Article nodes đều đã có vector sẵn!")

    # 4. Chuẩn bị dữ liệu nạp vào Qdrant
    print("\n>> [BƯỚC 4] Nạp dữ liệu vào Qdrant...")
    qdrant_store = QdrantVectorStore(
        location=qdrant_location,
        collection_name=collection_name,
        model_name=model_name,
        dimension=dimension,
        create=True,
    )

    ids = []
    vectors = []
    documents = []
    metadatas = []

    for a in articles:
        nid = a["node_id"]
        doc = existing_texts.get(nid) or build_enriched_text(a, node_map)
        vec = existing_vectors[nid]

        ids.append(nid)
        vectors.append(vec)
        documents.append(doc)
        metadatas.append({
            "node_id": nid,
            "label": "Article",
            "document_id": a["document_id"],
            "number": str(a.get("number", "")),
            "title": a.get("title") or "",
        })

    start_time = time.time()
    qdrant_store.upsert(ids, vectors, documents, metadatas)
    qdrant_store.update_metadata({
        "corpus_hash": corpus_hash,
        "total_articles": len(ids),
        "migrated_from": "chroma",
        "migrated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    elapsed = time.time() - start_time
    total_in_qdrant = qdrant_store.count()
    print(f">> Đã nạp thành công {len(ids):,} vectors vào Qdrant trong {elapsed:.2f}s!")
    print(f">> Tổng số records hiện tại trong Qdrant collection '{collection_name}': {total_in_qdrant:,}")

    # 5. Kiểm tra truy vấn mẫu (Sanity Query Test)
    print("\n>> [BƯỚC 5] Chạy truy vấn kiểm thử (Sanity Check)...")
    sample_query = "quy định về mang thai hộ vì mục đích nhân đạo"
    embedder = NodeEmbedder(model_name=model_name)
    embedder.load_model()
    q_vec = embedder.encode_query(sample_query)

    hits = qdrant_store.query(q_vec, top_k=3)
    print(f">> Câu truy vấn: '{sample_query}'")
    for rank, h in enumerate(hits, 1):
        print(f"  {rank}. [{h['node_id']}] (Score: {h['score']:.4f}) - {h['metadata'].get('title')}")

    qdrant_store.close()
    print("\n" + "=" * 70)
    print("   MIGRATION SANG QDRANT HOÀN TẤT THÀNH CÔNG 100%!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
