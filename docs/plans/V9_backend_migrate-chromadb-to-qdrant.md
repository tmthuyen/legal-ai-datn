# V8 — Di Chuyển Vector Store Từ ChromaDB Sang Qdrant (1.045 Điều Luật)

> **Trạng thái:** Hoàn thành 100% (Đã migrate dữ liệu, pass full unit test & sync verifier)  
> **Thời gian:** 2026-11-28  
> **Phạm vi (Scope):** `backend` (`backend/src/vector/**`, `backend/src/common/**`, `backend/scripts/**`, `backend/tests/**`, `backend/src/eval/**`)  
> **Nguyên tắc thiết kế:**
>
> 1. **Hiệu năng & Khả năng mở rộng:** Qdrant là vector search engine hiệu năng cao (Rust-based), tối ưu bộ nhớ, hỗ trợ lọc metadata trước (payload filtering) và sẵn sàng chuyển đổi giữa chế độ local file và client-server không cần sửa code logic.
> 2. **Tính bảo toàn định danh (ID Determinism & Invariant Data Contract):** Qdrant bắt buộc Point ID dạng `uint64` hoặc `UUID`. Dùng hàm băm xác định `UUID5` từ `node_id` pháp lý (vd: `BLDS_2015_D20` -> deterministic UUID), đồng thời lưu giữ nguyên gốc `node_id` trong Payload. Lớp interface trả về hoàn toàn trong suốt với `node_id` gốc để không làm ảnh hưởng đến Graph Traversal và Legal Rule Engine.
> 3. **Đồng bộ toàn vẹn dữ liệu (Corpus Parity 100%):** Nhúng và lập chỉ mục đầy đủ toàn bộ 1.045 Điều luật (BLDS 2015, Hiến pháp 2013, Luật Hôn nhân & Gia đình 2014 và các Nghị định) vào Qdrant và file cache `.npz`.
> 4. **Khả năng tương thích ngược & Rollback an toàn:** Giữ cấu trúc abstract qua `Container` và cấu hình qua `setting_config.py`, cho phép chuyển đổi linh hoạt giữa `qdrant`, `chroma`, `neo4j`.

---

## 1. Động Lực & Mục Tiêu

### 1.1. Động lực

- ChromaDB chạy trên SQLite/hnswlib local đôi khi gặp hạn chế về tài nguyên đồng thời, định dạng file nhị phân khóa lock khi nhiều tiến trình truy cập, và khó mở rộng sang cụm phân tán trong môi trường production.
- Qdrant cung cấp engine vector hiện đại, quản lý segment hiệu quả, hỗ trợ bộ lọc tải trọng (payload filtering) cực nhanh và hỗ trợ cấu hình đa môi trường:
  - **Local file mode:** Chạy trực tiếp qua thư mục `data/qdrant/` (thích hợp cho dev, test local không bắt buộc bật Docker).
  - **Server mode:** Kết nối qua URL `http://localhost:6333` (chuẩn bị sẵn cho triển khai Docker/Kubernetes).

### 1.2. Mục tiêu kỹ thuật

1. Hiện thực adapter `QdrantVectorStore` tương thích hoàn toàn với interface vector store hiện tại của hệ thống.
2. Hỗ trợ chuyển đổi tự động và 2 chiều giữa định danh pháp lý (`node_id`) và Qdrant Point ID (`UUID5`).
3. Chuẩn hóa điểm cosine: chuyển khoảng $[-1.0, 1.0]$ của Qdrant về khoảng $[0.0, 1.0]$ tương thích với chuẩn Chroma trước đây:  
   $$\text{normalized\_score} = \frac{1.0 + \text{raw\_score}}{2.0}$$
4. Di chuyển dữ liệu: Trích xuất và nạp đầy đủ **1.045 Điều luật** vào collection `legal_articles`. Bổ sung 133 Điều luật thuộc `LUAT_HNGD_2014` vào cache embeddings `.npz`.
5. Đấu nối `QdrantVectorStore` vào Dependency Injection `container.py` cho `SemanticSearcher`, `HybridSearcher`, `EmbeddingPipeline`.
6. Đảm bảo toàn bộ 22/22 unit tests và script kiểm tra đồng bộ đồ thị - vector (`sync_verifier.py`) đạt 100% PASS.

---

## 2. Chi Tiết Kiến Trúc & Triển Khai

### 2.1. Adapter `QdrantVectorStore` (`backend/src/vector/qdrant_store.py`)

- **Khởi tạo & Kết nối linh hoạt:**
  - Nếu `location` là HTTP/HTTPS URL $\rightarrow$ Khởi tạo `QdrantClient(url=...)`.
  - Nếu `location` là đường dẫn thư mục $\rightarrow$ Khởi tạo `QdrantClient(path=...)`.
  - Tự động tạo collection với tham số `VectorParams(size=dimension, distance=Distance.COSINE)`.
- **Ánh xạ ID xác định (Deterministic Point ID):**

  ```python
  NAMESPACE_QDRANT = uuid.NAMESPACE_DNS

  def _to_uuid(self, node_id: str) -> str:
      return str(uuid.uuid5(NAMESPACE_QDRANT, node_id))
  ```

  - Khi lưu (`upsert`): Sinh `point_id = _to_uuid(node_id)`, đồng thời nạp `node_id` chuỗi vào `payload`.
  - Khi truy vấn (`query`): Lấy `payload["node_id"]` làm `node_id` trả về.
  - Khi tra cứu (`get`): Cho phép tra cứu trực tiếp bằng danh sách `node_id` dạng chuỗi truyền thống bằng cách tự động hash sang UUID để truy xuất từ Qdrant.

- **Proxy tương thích ngược (`_QdrantCollectionProxy`):**
  - Cung cấp `collection.metadata` và `collection.modify()` đọc/ghi file `legal_articles_meta.json` để tương thích hoàn toàn với các script kiểm tra vốn viết cho Chroma trước đây.

### 2.2. Cấu hình & DI Wiring

- **`backend/src/common/setting_config.py`:**
  - Thêm cấu hình:
    - `qdrant_path: Path = BACKEND_ROOT / "data" / "qdrant"`
    - `qdrant_url: Optional[str] = None`
    - `qdrant_collection: str = "legal_articles"`
    - `vector_backend: Literal["neo4j", "chroma", "qdrant"] = "qdrant"`
- **`backend/.env`:**
  - Thiết lập mặc định: `VECTOR_BACKEND=qdrant` và `QDRANT_COLLECTION=legal_articles`.
- **`backend/src/common/container.py`:**
  - Nâng cấp `_build_vector_store()` để khởi tạo `QdrantVectorStore` khi `settings.vector_backend == "qdrant"`.
  - Tự động inject vào `SemanticSearcher` và `HybridSearcher`.
- **`backend/src/vector/embedding_pipeline.py` & `backend/scripts/embed_nodes.py`:**
  - Bổ sung tùy chọn backend `qdrant`.
  - Hỗ trợ pipeline nạp vector trực tiếp từ cache `.npz` hoặc nhúng mới qua HuggingFace Transformer.

---

## 3. Dữ Liệu & Quy Trình Di Chuyển (Migration)

### 3.1. Kịch bản di chuyển (`backend/scripts/migrate_chroma_to_qdrant.py`)

1. **Tải dữ liệu từ cache:**
   - Nạp 912 vectors sẵn có từ `data/embeddings/article_embeddings_darklethelong_vnlegal-lal_enriched.npz`.
2. **Bổ sung văn bản thiếu (`LUAT_HNGD_2014`):**
   - Đọc 133 Điều luật của Luật Hôn nhân & Gia đình 2014 từ `data/processed/nodes.json`.
   - Sinh enriched passage text (`{citation}. {title}. {full_text}`).
   - Nhúng dense vector 1024 chiều qua model `darklethelong/vnlegal-lal`.
3. **Upsert vào Qdrant:**
   - Đẩy tổng cộng **1.045 / 1.045 điều luật** vào collection `legal_articles` của Qdrant.
4. **Cập nhật File Cache `.npz` & SHA-256 Hash:**
   - Ghi lại toàn bộ 1.045 embeddings, danh sách `node_ids`, văn bản enriched, và tính toán lại corpus hash chuẩn:
     $$\text{corpus\_hash} = \text{f93b85ba901d3517810525f375cd3f278d65a63af687a7fa62893c6eb16a98b0}$$
   - Đồng bộ metadata giữa Qdrant (`legal_articles_meta.json`) và cache `.npz`.

---

## 4. Kiểm Thử & Xác Thực (Verification)

### 4.1. Unit Tests (`backend/tests/unit/vector/test_qdrant_store.py`)

- `test_qdrant_init_and_metadata`: Kiểm tra khởi tạo collection, lưu và đọc metadata.
- `test_qdrant_upsert_and_count`: Kiểm tra tính idempotent, số lượng vectors sau khi upsert.
- `test_qdrant_query_cosine_and_score_range`: Kiểm tra độ chính xác của vector search và khoảng điểm $[0.0, 1.0]$.
- `test_qdrant_document_filter`: Kiểm tra tiền lọc điều kiện `document_id`.
- `test_qdrant_get_by_ids`: Kiểm tra khả năng tra cứu ngược bằng chuỗi `node_id`.
- **Kết quả:** `5/5 tests PASSED`. Toàn bộ `tests/unit`: **22/22 tests PASSED** trong 1.20s.

### 4.2. Kiểm tra đồng bộ Retrieval (`backend/src/graph/sync_verifier.py`)

Chạy kiểm tra tính đồng nhất giữa Knowledge Graph (Neo4j/JSON), Cache NPZ và Qdrant DB:

```powershell
python backend/src/graph/sync_verifier.py
```

- **Kết quả:**
  - Status: **PASS**
  - Node count: `1045` Articles đồng nhất trên cả 3 nguồn.
  - Corpus Hash: Khớp chính xác `f93b85ba901d...`

### 4.3. Kiểm thử luồng thực tế (Live Query Smoke Test)

- **Truy vấn:** `"người thành niên từ đủ bao nhiêu tuổi"`
- **Kết quả trả về:**
  - Top 1: `node_id: "BLDS_2015_D20"` (Điều 20 Bộ luật Dân sự 2015: Người thành niên) — Score: `0.8540`.
  - Top 2: `node_id: "BLDS_2015_D21"` (Điều 21 Bộ luật Dân sự 2015: Người chưa thành niên) — Score: `0.7904`.
  - Định dạng `node_id` trả về: Giữ nguyên chuỗi string gốc, tương thích 100% với Neo4j Hydration và Fact Extractor.

---

## 5. Danh Sách Tệp Thay Đổi & Tạo Mới

| Loại    | Đường dẫn tệp                                         | Mô tả                                                          |
| ------- | ----------------------------------------------------- | -------------------------------------------------------------- |
| **Mới** | `backend/src/vector/qdrant_store.py`                  | Lớp Vector Store Adapter cho Qdrant (local file & remote URL). |
| **Mới** | `backend/scripts/migrate_chroma_to_qdrant.py`         | Script nạp dữ liệu từ Chroma/NPZ và nhúng bổ sung vào Qdrant.  |
| **Mới** | `backend/tests/unit/vector/test_qdrant_store.py`      | Bộ test tự động cho Qdrant store.                              |
| **Mới** | `docs/plans/V8_backend_migrate-chromadb-to-qdrant.md` | Tài liệu đặc tả và tổng kết di chuyển Qdrant.                  |
| **Sửa** | `backend/src/common/setting_config.py`                | Thêm tham số Qdrant và đổi backend mặc định sang `qdrant`.     |
| **Sửa** | `backend/src/common/container.py`                     | Khởi tạo và inject `QdrantVectorStore` vào `SemanticSearcher`. |
| **Sửa** | `backend/src/vector/embedding_pipeline.py`            | Hỗ trợ nạp vector cho `qdrant`.                                |
| **Sửa** | `backend/scripts/embed_nodes.py`                      | Mở rộng CLI hỗ trợ lựa chọn `qdrant`.                          |
| **Sửa** | `backend/src/eval/runner_eval.py`                     | Bổ sung vector store `qdrant` cho đánh giá Benchmark.          |
| **Sửa** | `backend/src/graph/sync_verifier.py`                  | Thêm kiểm tra xác thực đồng bộ cho Qdrant.                     |
| **Sửa** | `backend/.env` & `backend/.env.example`               | Đặt biến môi trường `VECTOR_BACKEND=qdrant`.                   |
| **Sửa** | `docs/plans/PLAN_INDEX.md`                            | Cập nhật mục lục plan V8.                                      |
