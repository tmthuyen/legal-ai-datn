# V1 — Truy xuất theo trích dẫn cấu trúc luật (Target Parsing → Validate → Graph Retrieval)

> Trạng thái: **Draft — chờ duyệt**
> Người thực hiện: dev
> Phạm vi: Bước 1 — từ câu hỏi có trích dẫn (Điều/Khoản/Điểm/Chương...) → parse cấu trúc → validate → truy vấn đồ thị lấy nội dung + luật liên quan + nguồn gốc tài liệu.
> Nơi thử nghiệm: `backend/notebooks/04_retrieval.ipynb`

---

## 1. Mục tiêu

Cho câu hỏi tự nhiên có trích dẫn vị trí luật, hệ thống phải:

1. **Parse** câu hỏi thành cấu trúc `target` chuẩn hoá (document, part, chapter, section, subsection, article, clause, point) + `query_text` + `question_text`.
2. **Validate** cấu trúc: có `document`, đúng thứ bậc cha ↔ con, giá trị từng cấp hợp lệ.
3. **Resolve** `target` xuống một node thực trên đồ thị Neo4j (không chỉ tái tạo `node_id`).
4. **Truy vấn nội dung luật** tại node đích (kèm tổ tiên/hậu duệ: Điều → Khoản → Điểm).
5. **Truy vấn luật liên quan** qua các quan hệ pháp lý (`REFERENCES`, `IMPLEMENTS`, `INTERPRETED_BY`, `AMENDS`, `RELATED_TO`...).
6. **Truy vết nguồn gốc tài liệu** (document gốc: file, số hiệu, ngày hiệu lực, trạng thái, URL nguồn) lấy trực tiếp từ node `Document` trên đồ thị.

### Ví dụ đầu vào / đầu ra mong muốn

Đầu vào (đã parse):

```json
{
  "query_text": "Chương I của Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013 quy định về vấn đề gì?",
  "question_text": "Chương I của  quy định về vấn đề gì?",
  "target": {
    "part": null,
    "chapter": "I",
    "section": null,
    "subsection": null,
    "article": null,
    "clause": null,
    "point": null,
    "document": "Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013"
  }
}
```

Đầu ra mong muốn (định hướng):

```json
{
  "resolved": {
    "document_id": "HIEN_PHAP_2013",
    "node_id": "HIEN_PHAP_2013_CH1",
    "breadcrumb": [
      { "type": "Document", "node_id": "HIEN_PHAP_2013", "title": "Hiến pháp..." },
      { "type": "Chapter",  "node_id": "HIEN_PHAP_2013_CH1", "number": "I", "title": "CHẾ ĐỘ CHÍNH TRỊ" }
    ]
  },
  "content": {
    "text": null,
    "children": [ { "type": "Article", "node_id": "HIEN_PHAP_2013_D1", "full_text": "..." } ]
  },
  "related": [
    { "relation": "REFERENCES", "source_id": "...", "target_id": "...", "evidence": "...", "confidence": 1.0 }
  ],
  "provenance": {
    "source_file": "Hien_phap_nam_2013.docx",
    "so_hieu": "Không số",
    "issuer": "Quốc hội",
    "effective_from": "2014-01-01",
    "effective_to": null,
    "status": "HET_HIEU_LUC_MOT_PHAN",
    "source_url": "https://vbpl.vn/..."
  }
}
```

---

## 2. Phạm vi

**Trong phạm vi (V1):**

- Parse + validate + resolve + retrieval + provenance cho bộ 5 văn bản đang có trong corpus.
- Trả về cấu trúc JSON qua notebook (chưa cần API).
- Bao phủ các đường dẫn phân cấp: chương-only, điều-only, khoản, điểm, và tổ hợp.

**Ngoài phạm vi (để V2+):**

- Gọi LLM sinh câu trả lời cuối + diễn giải (đó là Bước 2 — reasoning).
- Kiểm chứng phản ví dụ / NLI / confidence (Bước 3).
- Fine-tune model parse câu hỏi (nếu chọn hướng LLM).
- Truy xuất semantic/vector (BGE-M3 + ChromaDB) — có thể thêm sau, V1 ưu tiên graph.

---

## 3. Luồng xử lý (Pipeline)

```
Câu hỏi người dùng
      │
      ▼
[1] PARSE        ExtractorLegalQuery.extract(query, document)
      │          → { query_text, question_text, target{...} }
      ▼
[2] VALIDATE     LegalHierarchy.validate()
      │          - document bắt buộc
      │          - point ⟹ clause ⟹ article
      │          - subsection ⟹ section
      │          - chuẩn hoá giá trị (roman, hoa/thường, kiểu number)
      ▼
[3] RESOLVE DOC  DocumentResolver.resolve(target.document)
      │          - alias → document_id (documents_config.json)
      │          - kiểm tra node :Document tồn tại trong Neo4j
      ▼
[4] RESOLVE NODE TargetResolver.resolve(document_id, target)
      │          - traversal CONTAINS + MATCH theo (type, number)
      │          - trả về node_id sâu nhất khớp target
      ▼
[5] RETRIEVE     ContentRetriever
      │          - node content (text/full_text)
      │          - ancestors (breadcrumb) + descendants
      ▼
[6] RELATED      ReferenceRetriever (1–2 hop)
      │          - REFERENCES / IMPLEMENTS / INTERPRETED_BY / AMENDS / RELATED_TO
      │          - kèm evidence, source_type, confidence
      ▼
[7] PROVENANCE   Document provenance từ node :Document
      │          - source_file, source_url, so_hieu, effective_from/to, status...
      ▼
Kết quả JSON (RetrievalResult)
```

---

## 4. Hiện trạng code (As-is)

| Thành phần | File | Trạng thái |
| --- | --- | --- |
| Parse cấu trúc phân cấp | `src/retrieval/legal_query.py` (`ExtractorLegalQuery.extract`) | **Có** — trả `context`; chưa đúng key `target` |
| Schema phân cấp + validate | `src/common/schemas.py` (`LegalHierarchy`, `LegalHierarchyPatterns`, `validate`) | **Có** — validate cơ bản |
| Kết nối Neo4j | `src/graph/neo4j_client.py` | **Có** |
| Repository/service graph | `src/graph/graph_repository.py`, `graph_service.py` | **Có** — chỉ find-all & relationship cơ bản |
| Import graph | `graph/import_neo4j.py` | **Có** (đã nạp được) |
| Alias + provenance nguồn | `data/documents_config.json` (aliases, metadata) | **Có dữ liệu**, chưa có code đọc |
| Resolve doc/node, retrieval, provenance | — | **Chưa có** |
| Notebook 04 | `notebooks/04_retrieval.ipynb` | Đang sinh dataset truy xuất, chưa nối graph |

### Đặc điểm dữ liệu quan trọng (ràng buộc thiết kế)

- **node_id convention:** `HIEN_PHAP_2013`, `..._P1`, `..._CH1`, `..._CH3_M1`, `..._CH13_M1_TM1`, `..._D1`, `..._D2_K1`, `..._D27_K1_DIEM_A`.
- **CẢNH BÁO:** Chapter `number = "I"` nhưng `node_id = "..._CH1"` (đánh số tuần tự, KHÔNG theo số La Mã). ⇒ **Không nên tái tạo node_id bằng chuỗi**; phải resolve qua đồ thị.
- **Kiểu `number` không nhất quán:** `Article`/`Clause` là **int**, còn `Chapter`/`Section`/`SubSection`/`Point` là **string**. Cần chuẩn hoá khi so khớp.
- Quan hệ `CONTAINS` thể hiện cây phân cấp; node con có `parent_id`, node `Document` có `document_id`.
- Document node chứa đầy đủ provenance: `source_file`, `source_url`, `so_hieu`, `issuer`, `effective_from`, `effective_to`, `status`, `metadata_source`, `verified_at`.

---

## 5. Thiết kế

### 5.1. Chuẩn hoá output parse (`src/retrieval/legal_query.py`)

- Đổi key trả về từ `context` → `target` cho khớp format đề bài.
- Thêm bước **normalize**:
  - `chapter/section/subsection/part`: giữ roman nhưng uppercase (`i` → `I`).
  - `point`: lowercase (`A` → `a`).
  - `article/clause`: chuẩn hoá về string số (`"03"` → `"3"`).
- Không thay đổi logic regex hiện có.

### 5.2. Validate (`src/common/schemas.py`)

Mở rộng `LegalHierarchy.validate()` (giữ exception hiện tại, bổ sung):

- `document` bắt buộc (đã có).
- `point ⟹ clause ⟹ article` (đã có), `subsection ⟹ section` (đã có).
- Bổ sung: `section ⟹ chapter || part`, `subsection` không thể có nếu không có `section` (đã có).
- Thêm mã lỗi qua `CustomException.error_code` (vd `MISSING_DOCUMENT`, `INVALID_HIERARCHY`).
- Thêm hàm `normalize()` tách riêng để test độc lập.

### 5.3. Resolve document — `DocumentResolver` (MỚI)

File mới: `src/retrieval/document_resolver.py`

- Đọc `backend/data/documents_config.json`.
- Build map `alias (chuẩn hoá) → document_id` + `document_id → metadata`.
- Chuẩn hoá alias: lowercase, gộp khoảng trắng, bỏ ký tự đặc biệt (dùng `clean_text_utils`).
- API: `resolve_document(name) -> document_id`; raise `CustomException(error_code="DOCUMENT_NOT_FOUND")` nếu không khớp.
- Xác nhận tồn tại thật trên graph: `MATCH (d:Document {document_id}) RETURN d`.

### 5.4. Resolve node đích — `TargetResolver` (MỚI)

File mới: `src/retrieval/target_resolver.py`

Chiến lược (canonical): **traversal theo `CONTAINS` + MATCH `type` + `number`**, đi từ cấp cao nhất xuống cấp sâu nhất có trong target.

Cypher tổng quát sinh động (chỉ thêm cấp nào có trong target), ví dụ với `chapter=CH1`, `article=3`:

```cypher
MATCH (d:LegalNode {node_id: $document_id})
MATCH (d)-[:CONTAINS*1..7]->(n:Article {number: $article})
WHERE n.document_id = $document_id
RETURN n.node_id AS node_id
```

Với nhiều cấp, dùng mệnh đề `MATCH (parent)-[:CONTAINS]->(child {type, number})` nối tiếp thay vì `*` để kiểm soát đúng cấp (tránh khớp nhầm Article của chapter khác).

- `type` cố định theo cấp: part→`Part`, chapter→`Chapter`, ... point→`Point`.
- `number` đã normalize (ép string hoặc int tuỳ cấp; tốt nhất dùng `toString(n.number) = $val`).
- Fallback: nếu match theo `number` rỗng, thử match theo `title` (contains, không dấu).
- Trả về `TargetResolution { node_id, type, level }`; raise `TARGET_NOT_FOUND` kèm thông tin cấp bị lệch.

> Ghi chú: có thể thêm fast-path tái tạo `node_id` cho các cấp Điều/Khoản/Điểm (`_D{n}_K{n}_DIEM_{X}`), nhưng **luôn verify bằng graph trước khi dùng**.

### 5.5. Truy vấn nội dung — `ContentRetriever`

Bổ sung method vào repository/service:

- `get_node(node_id)` — lấy node đích + props (`text`, `full_text`, `title`, `number`).
- `get_ancestors(node_id)` — dùng `parent_id` hoặc `[:CONTAINS*]` ngược, sắp xếp từ Document → node.
- `get_descendants(node_id)` — `[:CONTAINS*]` xuôi, sắp theo thứ tự cây.

Trả về:
- `content.text` (nếu có) hoặc `content.children[]` (Điều → Khoản/Điểm), ưu tiên `full_text` cho Article.

### 5.6. Truy vấn luật liên quan — `ReferenceRetriever`

- Query 1–2 hop:
  - outgoing: `(n)-[r:REFERENCES|IMPLEMENTS|AMENDS|RELATED_TO]->(m)`
  - incoming: `(m)-[r:INTERPRETED_BY|REPLACED_BY|RELATED_TO]->(n)`
- Trả về: `relation`, `source_id`, `target_id`, `evidence`, `source_type`, `confidence`.
- Giới hạn `limit` + tham số `hops` cấu hình được.

### 5.7. Truy vết nguồn gốc — `ProvenanceService`

- `get_document_provenance(document_id)`:
  `MATCH (d:Document {node_id: $document_id}) RETURN d.source_file, d.source_url, d.so_hieu, d.issuer, d.effective_from, d.effective_to, d.status, d.metadata_source, d.verified_at`.
- (Tùy chọn) bổ sung từ `documents_config.json` nếu graph thiếu field nào.

### 5.8. Orchestrator — `RetrievalService` (MỚI)

File mới: `src/retrieval/retrieval_service.py`

- `retrieve(query_text, document) -> RetrievalResult` gọi tuần tự [1]→[7].
- Xuất một object/JSON thống nhất (dùng Pydantic model trong `src/common/schemas.py`).

### 5.9. Response schema (`src/common/schemas.py`)

Thêm models: `HierarchyTarget`, `ResolvedTarget`, `BreadcrumbItem`, `ContentResult`, `RelatedLaw`, `ProvenanceInfo`, `RetrievalResult`.

---

## 6. Phân bố code (Where code goes)

```
backend/
├── src/
│   ├── common/
│   │   └── schemas.py                     # [SỬA] add normalize(), validate() rules, response models
│   ├── retrieval/
│   │   ├── legal_query.py                 # [SỬA] context → target, normalize output
│   │   ├── document_resolver.py           # [MỚI] alias → document_id
│   │   ├── target_resolver.py             # [MỚI] target → node_id qua CONTAINS
│   │   ├── retrieval_service.py           # [MỚI] orchestrator [1]→[7]
│   │   ├── graph_traverse.py              # [SỬA] hoặc đặt ContentRetriever/ReferenceRetriever ở đây
│   │   ├── semantic.py / reranker.py      # (giữ trống, V2)
│   │   └── hybrid.py                      # (giữ trống, V2)
│   ├── graph/
│   │   ├── graph_repository.py            # [SỬA] add Cypher: resolve/resolve_node/ancestors/descendants/refs/provenance
│   │   └── graph_service.py               # [SỬA] expose các method mới
│   └── api/
│       ├── api_schemas.py                 # [V2] request/response
│       └── routes/query.py                # [V2] POST /api/query
├── notebooks/
│   └── 04_retrieval.ipynb                 # [SỬA] thêm cell chạy end-to-end + test cases
└── data/
    └── documents_config.json              # [ĐỌC] alias + provenance
```

---

## 7. Task breakdown

### Phase 0 — Nền tảng parse & validate

- [ ] **T0.1** Sửa `ExtractorLegalQuery.extract` trả key `target` thay `context`; thêm `normalize()`.
  - Output khớp chính xác ví dụ đề bài.
- [ ] **T0.2** Mở rộng `LegalHierarchy.validate()` theo mục 5.2 + mã lỗi.
- [ ] **T0.3** Thêm Pydantic models trong `schemas.py` (mục 5.9).

### Phase 1 — Resolve

- [ ] **T1.1** `DocumentResolver`: alias → `document_id`, verify trên graph.
- [ ] **T1.2** `graph_repository.find_document(document_id)` + service.
- [ ] **T1.3** `TargetResolver`: sinh Cypher traversal theo các cấp có trong target; verify node tồn tại.
- [ ] **T1.4** `get_node`, `get_ancestors`, `get_descendants` trong repository/service.

### Phase 2 — Retrieval & Provenance

- [ ] **T2.1** `ContentRetriever`: gom text/full_text + children.
- [ ] **T2.2** `ReferenceRetriever`: REFERENCES/IMPLEMENTS/INTERPRETED_BY 1–2 hop + evidence.
- [ ] **T2.3** `ProvenanceService`: lấy provenance từ node `Document`.
- [ ] **T2.4** `RetrievalService.retrieve()` gộp toàn bộ, trả `RetrievalResult`.

### Phase 3 — Demo & test

- [ ] **T3.1** Notebook 04: cell khởi tạo `Neo4jClient` → `RetrievalService`; chạy ví dụ "Chương I Hiến pháp 2013".
- [ ] **T3.2** Test cases bắt buộc (bảng mục 8) — chạy tay trong notebook và ghi kết quả.
- [ ] **T3.3** (Tùy chọn) Script `scripts/test_retrieval.py` chạy tự động.

### Phase 4 — API (sau khi V1 ổn định)

- [ ] **T4.1** `POST /api/query` nhận `{query_text, document}` → `RetrievalResult`.
- [ ] **T4.2** Cập nhật `src/api/server.py` + `routes/health.py` (đang trống).

---

## 8. Test cases & tiêu chí nghiệm thu

| # | Input | Kỳ vọng |
| --- | --- | --- |
| 1 | "Chương I của Hiến pháp ... 2013 quy định gì?" | resolve `HIEN_PHAP_2013_CH1`, trả title + danh sách Điều |
| 2 | "Điều 3 của Bộ luật Dân sự 2015" | resolve `BLDS_2015_D3`, trả `full_text` |
| 3 | "Khoản 2 Điều 3 BLDS 2015" | resolve `BLDS_2015_D3_K2`, trả text khoản |
| 4 | "Điểm a Khoản 1 Điều 27 BLDS 2015" | resolve `BLDS_2015_D27_K1_DIEM_A` |
| 5 | "Điểm a của BLDS 2015" (thiếu Khoản/Điều) | `INVALID_HIERARCHY` (point cần clause) |
| 6 | "Điều 999999 của Hiến pháp 2013" | `TARGET_NOT_FOUND` |
| 7 | "Luật Giao thông đường bộ 2008" | `DOCUMENT_NOT_FOUND` (ngoài corpus) |
| 8 | Document có REFERENCES | `related[]` chứa cạnh + evidence |
| 9 | Bất kỳ | `provenance` trả đủ source_file/source_url/effective_from/status |
| 10 | Alias "BLDS", "Hiến pháp 2013" | resolve đúng document_id |

**Tiêu chí nghiệm thu:** 10/10 case chạy được trong notebook 04, kết quả đúng cấu trúc `RetrievalResult`, không raise ngoài `CustomException` dự kiến.

---

## 9. Rủi ro & Câu hỏi mở (cần chốt trước khi code)

### Rủi ro

1. **node_id Chapter lệch số La Mã** (`I` → `CH1`) → đã xử lý bằng resolve qua graph, KHÔNG tái tạo chuỗi.
2. **Kiểu `number` int vs string** → dùng `toString(n.number)` khi so khớp.
3. **Alias trùng/thiếu** trong `documents_config.json` → cần kiểm tra trùng khóa, ưu tiên alias dài nhất/khớp chính xác.
4. **Dữ liệu có mojibake khi hiển thị** trên một số môi trường — cần đọc/ghi UTF-8 thống nhất (`sys.stdout.reconfigure(utf-8)`).
5. **Corpus nhỏ (5 văn bản)** → nhiều `REFERENCES` trỏ ra ngoài sẽ `unresolved`; cần trả về cả dẫn chiếu chưa resolve thay vì bỏ.

### Câu hỏi mở (chốt với người hướng dẫn/dev)

1. **Cơ chế parse câu hỏi:** tiếp tục dùng rule-based `ExtractorLegalQuery` (regex) hay chuyển sang **LLM trả JSON có schema** (Qwen fine-tuned ở notebook 05)? Điều này quyết định Phase 0.
   - *Đề xuất:* V1 dùng rule-based làm baseline, thêm interface `ParserProtocol` để cắm LLM sau.
2. **Định dạng nội dung trả về:** chỉ đoạn text tại node đích, hay lấy toàn bộ cây con (tất cả Điều trong Chương)?
   - *Đề xuất:* mặc định trả node + descendants 1 cấp, cấu hình `depth`.
3. **Độ sâu truy vết nguồn gốc:** chỉ tới Document gốc, hay cả file `.docx` + URL + `metadata_source`?
   - *Đề xuất:* trả tối đa các field provenance của node `Document`.
4. **Có cần kết nối ChromaDB/semantic ngay trong V1** cho câu hỏi không có trích dẫn chính xác không? (Hiện V1 ưu tiên graph.)

---

## 10. Thứ tự thực hiện đề xuất

1. Phase 0 (T0.1 → T0.3) — chốt schema/validate.
2. Phase 1 (T1.1 → T1.4) — resolve doc + node, verify bằng 2–3 case.
3. Phase 2 (T2.1 → T2.4) — retrieval + provenance, chạy notebook 04.
4. Phase 3 (T3.1 → T3.2) — full test 10 case.
5. Phase 4 — API (sau khi V1 được duyệt).
