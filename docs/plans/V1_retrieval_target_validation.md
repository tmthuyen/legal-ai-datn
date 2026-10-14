# V1 — Truy xuất theo trích dẫn cấu trúc luật (Parse → Validate → Resolve → Graph Retrieval)

> Trạng thái: **Đã triển khai (V1) — script kiểm thử chạy được**
> Người thực hiện: agent
> Cập nhật: 2026-10-14
> Module liên quan: `scripts/test_retrieval.py` (orchestrator + DocumentResolver + output formatter + FallbackSearch interface), `src/graph/{graph_service,graph_repository}.py`, `src/common/schemas.py`
> Còn lại: Phase 5 (nối `notebooks/04_retrieval.ipynb`), cài `FallbackSearch` semantic thật (`src/retrieval/semantic.py`).
> Phạm vi: Bước 1 (Retrieval) — từ câu hỏi có trích dẫn vị trí luật → parse cấu trúc + validate → resolve node trên đồ thị → trả nội dung + luật liên quan + nguồn gốc tài liệu đúng format.

---

## 1. Mục tiêu

Từ câu hỏi tự nhiên có trích dẫn vị trí luật, trả về một **tập node + quan hệ đáng tin** trên đồ thị. Output dùng được cho cả ba đích: **reasoning (Bước 2)**, **notebook kiểm tra**, và **service API** về sau.

Hệ thống phải:

1. **Parse** câu hỏi → `LegalHierarchy` (document, part, chapter, section, subsection, article, clause, point).
2. **Validate** cấu trúc (`LegalHierarchy.validate`).
3. **Resolve** document (tên → `document_id`) và **resolve node đích** trên đồ thị Neo4j.
4. **Truy vấn nội dung** node đích + tổ tiên (`parent`) + con (`children`) + hậu duệ (`descendants`).
5. **Truy vấn luật liên quan** qua quan hệ pháp lý (`REFERENCES`, `IMPLEMENTS`, `INTERPRETED_BY`, `AMENDS`, `RELATED_TO`...).
6. **Truy vết nguồn gốc** tài liệu (file, số hiệu, hiệu lực, trạng thái, URL nguồn) từ node `Document`.

**Nguyên tắc bất di bất dịch:** không resolve được node → trả kết quả rỗng/"không tìm thấy", **cấm bịa đặt thông tin luật**.

---

## 2. Cổng kiểm tra (2 gate) — điểm cốt lõi

Hai cổng **độc lập**; không gộp chúng lại:

| Gate              | Kiểm tra gì                                                                                                                              | Nếu ĐẠT                       | Nếu KHÔNG ĐẠT                                           |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- | ------------------------------------------------------- |
| **G1 — Cấu trúc** | `LegalHierarchy.validate(require_document)` — chỉ kiểm tra _hình dạng_ (document bắt buộc; `point→clause→article`; `subsection→section`; `section→chapter`) | build `target` → sang G2      | chuyển `FallbackSearch` (semantic)                      |
| **G2 — Resolve**  | Resolve document + `LegalGraphService.resolve_target_node()` trên graph                                                                  | duyệt graph, gom node/quan hệ | coi như không có kết quả → `FallbackSearch` (KHÔNG bịa) |

> Ghi chú: G1 hợp lệ **không** đảm bảo node tồn tại (ví dụ "Chương II BLDS" parse đúng nhưng node thật là `BLDS_2015_P1_CH2`). G2 mới quyết định thành/bại.

---

## 3. Luồng xử lý (Pipeline)

```
query_text
  │
  ├─(1) LegalQueryExtractor.extract_hierarchy(query_text, document?)
  │        ← regex baseline (V1) | fine-tune model (sau)
  │        → { query_text, hierarchy, valid_hierarchy }
  │
  ├─(2) G1: LegalHierarchy.validate(require_document=True|False)
  │        ├─ KHÔNG hợp lệ → FallbackSearch.search(...) ──► trả kết quả fallback
  │        └─ Hợp lệ
  │             ├─(3) DocumentResolver.resolve(document_name) → document_id
  │             │        (đọc aliases trong data/documents_config.json)
  │             ├─(4) G2: LegalGraphService.resolve_target_node(document_id, target)
  │             │        ├─ None → KHÔNG chạm node → FallbackSearch / trả rỗng (không bịa)
  │             │        └─ chạm node đích trên graph
  │             ├─(5) gom ngữ cảnh (chỉ node chạm được):
  │             │        cha (ancestors/breadcrumbs) + con (children) + con cháu (descendants)
  │             │        + related_laws + document provenance
  │             └─(6) format output (6 key) + sinh `citation` tuyệt đối cho mọi node
  │                      bằng LegalGraphService.get_citation_path(node_id)
```

**Nhánh fallback (G1 sai cấu trúc hoặc G2 không chạm được node):** `FallbackSearch` tìm kiếm **ngữ nghĩa** trên không gian **các document liên quan** (corpus/`related_documents`), rồi **build `node_id` từ cấu trúc parse + document** và **duyệt graph**. Node nào **chạm được** thì đưa vào `related_nodes` kèm cha/con/con cháu + `citation`; node không chạm được thì bỏ (không bịa).

**Trích dẫn tuyệt đối (verification):** mọi node đưa vào kết quả phải kèm `citation` lấy từ graph bằng `LegalGraphService.get_citation_path(node_id)`. Hàm service này **tái sử dụng** `LegalHierarchy.get_citation_path()` làm formatter: lấy phả hệ qua `get_ancestors` → `LegalHierarchy.from_ancestors(breadcrumbs)` → gọi formatter. **Không** format trực tiếp từ parse của câu hỏi (parse chỉ mô tả mục tiêu).

---

## 4. Định dạng output (bắt buộc)

```json
{
  "input": "Chương I của Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013 quy định về vấn đề gì?",
  "extracted_hierarchy": {
    "part": null,
    "chapter": "I",
    "section": null,
    "subsection": null,
    "article": null,
    "clause": null,
    "point": null,
    "document": "Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013"
  },
  "node_information": {
    "node_type": "Chapter",
    "parent_node_type": "Document",
    "citation_path": "Chương I của Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013",
    "postfix_node_id": "_CH1"
  },
  "related_documents": [
    {
      "document_id": "HIEN_PHAP_2013",
      "document_name": "Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013",
      "source_file": "...",
      "source_url": "...",
      "so_hieu": "...",
      "issuer": "...",
      "effective_from": "...",
      "effective_to": "...",
      "status": "...",
      "metadata_source": "...",
      "verified_at": "..."
    }
  ],
  "related_nodes": [
    {
      "number": "I",
      "parent_id": "HIEN_PHAP_2013",
      "full_text": null,
      "text": "Chế độ chính trị",
      "document_id": "HIEN_PHAP_2013",
      "title": "Chế độ chính trị",
      "node_id": "HIEN_PHAP_2013_CH1",
      "label": "Chapter",
      "labels": ["LegalNode", "Chapter"],
      "citation": "Chương I của Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013"
    },
    {
      "number": 1,
      "parent_id": "HIEN_PHAP_2013_CH1",
      "full_text": "Nước Cộng hòa xã hội chủ nghĩa Việt Nam là một nước độc lập, có chủ quyền, thống nhất và toàn vẹn lãnh thổ, bao gồm đất liền, hải đảo, vùng biển và vùng trời.",
      "text": "Nước Cộng hòa xã hội chủ nghĩa Việt Nam là một nước độc lập, có chủ quyền, thống nhất và toàn vẹn lãnh thổ, bao gồm đất liền, hải đảo, vùng biển và vùng trời.",
      "document_id": "HIEN_PHAP_2013",
      "title": null,
      "node_id": "HIEN_PHAP_2013_D1",
      "label": "Article",
      "labels": ["LegalNode", "Article"],
      "citation": "Điều 1 Chương I của Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013"
    }
  ],
  "relationships": [
    {
      "from_node_id": "HIEN_PHAP_2013",
      "to_node_id": "HIEN_PHAP_2013_CH1",
      "relationship_type": "CONTAINS"
    },
    {
      "from_node_id": "HIEN_PHAP_2013_CH1",
      "to_node_id": "HIEN_PHAP_2013_D1",
      "relationship_type": "CONTAINS"
    }
  ]
}
```

Quy ước trường:

- **`input`** — câu hỏi gốc.
- **`extracted_hierarchy`** — kết quả parse (giá trị `null` nếu không có cấp đó).
- **`node_information`** — node dựng từ cấu trúc parse, chính là `LegalHierarchy.get_all_info()`: `node_type` (cấp sâu nhất), `parent_node_type` (cấp cha theo parse), `citation_path` (trích dẫn theo parse), `postfix_node_id` (đuôi id, ví dụ `_CH1`). Đây **chỉ là mô tả mục tiêu**; định danh/trích dẫn tuyệt đối lấy từ graph qua `citation`.
- **`related_documents[]`** — provenance của document được resolve (thường 1 phần tử; thêm document liên quan qua `IMPLEMENTS`/`INTERPRETED_BY`/`REFERENCES`).
- **`related_nodes[]`** — chỉ chứa **node thực sự chạm được trên graph**: node đích (phần tử đầu) + cha + con + con cháu, khử trùng theo `node_id`.
  - `parent_id` = node cha **trực tiếp**; node cấp cao nhất (Chương/Phần) có `parent_id = document_id` (không phải `null`).
  - `full_text` chỉ `Article` mới có (= tiêu đề + toàn văn; Article không có tiêu đề riêng thì bằng `text`); các loại khác dùng `title`/`text`.
  - `citation` = **trích dẫn tuyệt đối** lấy từ graph, sinh bởi `LegalGraphService.get_citation_path(node_id)` (xem §5/§6).
- **`relationships[]`** — mảng quan hệ phẳng `{from_node_id, to_node_id, relationship_type}`. Đây là biểu diễn **chính**; **không** lặp lại quan hệ trong từng node (tránh trùng lặp).
- **`label`** = loại node suy từ `labels(n)` (bỏ `LegalNode`), map `Subsection → SubSection`; `labels` = nhãn thô từ graph. **Không** đọc property `type` (không tồn tại trên graph).

---

## 5. Hiện trạng code (As-is)

| Thành phần                    | File                                                                               | Trạng thái                                                                                                                                                        |
| ----------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Schema phân cấp + `validate`  | `src/common/schemas.py`                                                            | **Có** (còn lỗ hổng — xem §6)                                                                                                                                     |
| Extractor regex               | `src/retrieval/legal_query_extractor.py` (`LegalQueryExtractor.extract_hierarchy`) | **Có**                                                                                                                                                            |
| Extractor model               | cùng file (`extract_hierarchy_with_model`)                                         | **Stub** (chưa load model)                                                                                                                                        |
| Kết nối Neo4j                 | `src/graph/neo4j_client.py`                                                        | **Có**                                                                                                                                                            |
| Repository                    | `src/graph/graph_repository.py`                                                    | **Có** (`find_node_by_hierarchy`, `get_ancestors`, `get_children`, `get_descendants`, relationships, provenance)                                                  |
| Service                       | `src/graph/graph_service.py`                                                       | **Có** (`resolve_target_node`, `get_breadcrumbs`, `get_children`, `get_descendants`, `get_related_laws`, `get_document_provenance`, `get_full_retrieval_context`) |
| Import graph                  | `graph/import_neo4j.py`                                                            | **Có** (đã nạp)                                                                                                                                                   |
| Document resolver đọc aliases | `scripts/test_retrieval.py` (`DocumentResolver`)                                                 | **Có** (aliases + `ten_van_ban` + `document_id`; alias dài xét trước)                                                                                             |
| Output formatter (6 key)      | `scripts/test_retrieval.py` (`RetrievalOrchestrator`)                                            | **Có**                                                                                                                                                            |
| Hàm trích dẫn tuyệt đối       | `src/graph/graph_service.py`                                                                     | **Có** — `get_citation_path(node_id)` (map phả hệ → `LegalHierarchy.from_ancestors` → `LegalHierarchy.get_citation_path`)                                        |
| Orchestrator V1               | `scripts/test_retrieval.py` (`RetrievalOrchestrator`)                                            | **Có**                                                                                                                                                            |
| FallbackSearch (semantic)     | `scripts/test_retrieval.py` (`FallbackSearch` ABC + `NullFallbackSearch`)                        | **Interface có**, chưa cài semantic thật (`src/retrieval/semantic.py` vẫn rỗng)                                                                                  |
| Notebook 04                   | `notebooks/04_retrieval.ipynb`                                                                   | **Chưa nối graph** (V1 dùng `scripts/test_retrieval.py`)                                                                                                          |

> Lưu ý format: `get_full_retrieval_context` trả shape khác (`query_info / resolved / content / related / provenance / status`) và đọc `type` từ property (null). Cần **adapter** hoặc viết orchestrator riêng để ra đúng §4. Trích dẫn tuyệt đối phải qua `get_citation_path(node_id)` mới (dựng từ `get_ancestors` — phải sửa `x.type` → `labels(x)`).

---

## 6. Ràng buộc dữ liệu (dễ sai)

- **`node_id` không tái tạo được từ số hiển thị.** Chương đánh số **tuần tự** (`_CH1`), không theo La Mã (`Chương II` → `..._P1_CH2`). ⇒ Luôn resolve qua đồ thị, **không build chuỗi id** rồi query.
  - Mẫu: `Document={DOC}`, `Part={DOC}_P{n}`, `Chapter={DOC}[_P{p}]_CH{n}`, `Section={DOC}_CH{ch}_M{n}`, `SubSection={DOC}_CH{ch}_M{m}_TM{n}`, `Article={DOC}_D{n}`, `Clause={DOC}_D{d}_K{k}`, `Point={DOC}_D{d}[_K{k}]_DIEM_{A}`.
- **`type` chỉ là label** `:LegalNode:<Type>`, không phải property → dùng `labels(n)`.
- **Kiểu `number` không nhất quán**: `Article`/`Clause` = `int`; `Chapter`/`Section`/`SubSection`/`Point`/`Part` = `str`.
- **Nội dung Article ở `full_text`** (`text` chỉ là đoạn mở đầu); loại khác không có `full_text`.
- Relation whitelist: `CONTAINS, REFERENCES, IMPLEMENTS, INTERPRETED_BY, AMENDS, REPEALS, REPLACED_BY, RELATED_TO`.
- **`LegalHierarchy.get_node_type()` trả `"Subsection"`** nhưng label graph là `"SubSection"` → cần map khi format.
- **Lỗ hổng `validate()`**: đã bắt `section → chapter` (sửa 2026-10-14); còn thiếu: kiểm tra document có trong corpus; chuẩn hoá kiểu `number`.
- **Bug sẵn có**: `graph_repository.count_nodes_by_type` đọc `n.type` → trả null; `graph_service.get_full_retrieval_context` đọc `.get("type")` → null. `get_ancestors` **đã sửa** (2026-10-14): `type` suy từ `labels(x)` (bỏ `LegalNode`) và bổ sung `document_id` vào projection để `related_nodes` nhất quán.
- **`LegalHierarchy.get_citation_path()` (đã sửa 2026-10-14)**: đảo thứ tự code về **nhỏ → lớn** (Điểm → … → Phần) và sửa bug precedence (`... if self.document else ""`). Giờ **được tái sử dụng** làm formatter cho node graph qua `LegalGraphService.get_citation_path(node_id)` — service dựng `LegalHierarchy.from_ancestors(breadcrumbs)` rồi gọi formatter này.

---

## 7. Giả định cần kiểm chứng

- [x] `find_node_by_hierarchy` resolve đúng khi **thiếu cấp trung gian** (không nêu Phần/Mục) — verified với `Điều 1` + `Chương I` và `Điều 522` (đủ cấp).
- [x] Aliases trong `documents_config.json` phủ hết tên văn bản, kể cả tên đầy đủ ("Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013") — verified.
- [x] Lệch kiểu `number` không làm `find_node_by_hierarchy` trượt — verified (Chapter `str` "I", Article `int` 1).
- [x] **Nguồn `document`**: chốt (a) tham số + alias scan dự phòng (xem §9 Phase 0).

---

## 8. Phạm vi

**Trong phạm vi (V1):**

- Parse + validate + resolve + retrieval + provenance cho bộ 5 văn bản corpus.
- Trả JSON đúng §4 qua notebook (chưa cần API).
- Bao phủ: chương-only, điều-only, khoản, điểm, và tổ hợp.
- `FallbackSearch` dưới dạng **interface cắm được** (xem §9 Phase 0 để chốt mức cài đặt).

**Ngoài phạm vi (để V2+):**

- Gọi LLM sinh câu trả lời cuối + diễn giải (Bước 2 — reasoning).
- Kiểm chứng phản ví dụ / NLI / confidence (Bước 3).
- Fine-tune model parse câu hỏi (dùng regex ở V1).

---

## 9. Công việc (Task) — chia phase

### Phase 0 — Chốt thiết kế

- [x] Chốt **nguồn `document`**: (a) tham số truyền vào (`document_hint`) + alias scan dự phòng từ câu hỏi.
- [x] Chốt **mức cài đặt `FallbackSearch`**: (a) chỉ định nghĩa interface (`NullFallbackSearch` trả rỗng); semantic thật để V2.
- [x] Chốt `require_document=True` cho G1 (khi đã resolve được document).
- [x] Chốt **dạng trích dẫn tuyệt đối**: (a) **nhỏ → lớn** (Điểm → … → Phần + văn bản); phần văn bản dùng `title` (ten_van_ban).

### Phase 1 — DocumentResolver

- [x] Viết resolver đọc `data/documents_config.json` (aliases + metadata) → `document_id` (`DocumentResolver`).
- [x] Không khớp → trả `None` (không fallback sai về document mặc định).

### Phase 2 — Orchestrator retrieval + service citation

- [x] Gọi `LegalQueryExtractor.extract_hierarchy` → `LegalHierarchy`.
- [x] G1: `validate` → nhánh invalid gọi `FallbackSearch`.
- [x] G2: `resolve_target_node` → nhánh not-found trả rỗng/fallback.
- [x] Gom ngữ cảnh (chỉ node chạm được): `get_breadcrumbs` + `get_children` + `get_descendants` + `get_related_laws` + `get_document_provenance`.
- [x] Suy `label` từ `labels()`; map `Subsection → SubSection`.
- [x] Thêm `LegalGraphService.get_citation_path(node_id)`: dựng **trích dẫn tuyệt đối** từ `get_ancestors` + tên Document (tái dùng `LegalHierarchy.get_citation_path`).
- [x] Sửa `graph_repository.get_ancestors`: `x.type` → suy từ `labels(x)`; thêm `document_id` vào projection.

### Phase 3 — Output formatter

- [x] Dựng **6 key**: `input / extracted_hierarchy / node_information / related_documents / related_nodes / relationships` đúng §4.
- [x] `node_information` = `LegalHierarchy.get_all_info()` (node_type, parent_node_type, citation_path, postfix_node_id), map `Subsection → SubSection`.
- [x] Tính `parent_id` từ breadcrumbs; node cấp cao nhất → `document_id`.
- [x] `full_text` cho Article, `text`/`title` cho loại khác.
- [x] Gắn `citation` cho mọi node trong `related_nodes` qua `get_citation_path(node_id)`.
- [x] Gộp quan hệ vào mảng `relationships` phẳng, khử trùng lặp `(from, type, to)`.

### Phase 4 — Fallback interface

- [x] Định nghĩa interface `FallbackSearch` (nhận `query_text + hierarchy + related_document_ids` → trả danh sách node chạm được).
- [x] Luồng fallback: node chạm được thì gom cha/con/con cháu + `citation`; không chạm được thì bỏ.
- [x] Cài đặt theo mức (a): `NullFallbackSearch` trả rỗng (semantic thật ở V2).

### Phase 5 — Nối notebook 04

- [ ] Nối orchestrator vào `notebooks/04_retrieval.ipynb` (cwd `backend/notebooks`) — **chưa làm**, V1 chạy bằng `scripts/test_retrieval.py`.
- [ ] Chạy thử vài truy vấn mẫu cho mỗi pattern phân cấp (đã chạy trong script, xem §11).

### Phase 6 — Kiểm thử & tài liệu

- [x] Bộ test thủ công (script) cho từng pattern: chương-only, điều-only, khoản, điểm, tổ hợp, và các case thất bại (`scripts/test_retrieval.py`).
- [x] Ghi lại kết quả thực tế vào plan (xem §11).

---

## 10. Not Doing (và lý do)

- **Không tự dựng `node_id` bằng chuỗi** rồi query — sai với đánh số tuần tự + tiền tố Phần (dùng graph resolve).
- **Không sinh câu trả lời LLM** — đó là Bước 2 (reasoning).
- **Không verification / counterfactual** — Bước 3.
- **Không fine-tune model parse** trong V1 — dùng regex baseline, thay model sau qua cùng interface.
- **Không lặp quan hệ trong mỗi node** — dùng mảng `relationships` phẳng ở cấp output.
- **Không format trích dẫn từ dữ liệu parse** — trích dẫn tuyệt đối sinh từ graph qua `LegalGraphService.get_citation_path(node_id)` (tái dùng `LegalHierarchy.get_citation_path`, nhưng nguồn dữ liệu là phả hệ đồ thị).

---

## 11. Kết quả thực tế (2026-10-14)

Đã triển khai và chạy `python scripts/test_retrieval.py` với Neo4j local (`legalai`, `3,472 nodes / 3,959 relations`).

| Case                                                    | Kết quả                                                                                                                        |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `Nội dung Điều 1 ... Hiến pháp ... 2013` (điều-only)    | Resolve `HIEN_PHAP_2013_D1`; `related_nodes` = D1 + Chương I; citation đúng                                                    |
| `Điều 1 thuộc Chương I ... Hiến pháp ...` (tổ hợp)      | Resolve `HIEN_PHAP_2013_D1`; `node_type=Article`, `parent_node_type=Chapter`                                                    |
| `Chương I của Hiến pháp ...` (chương-only)              | Resolve `HIEN_PHAP_2013_CH1`; `related_nodes` = Chương I + 13 Điều + toàn bộ Khoản con cháu; relationships = 37 cạnh CONTAINS |
| `Điều 522 của Bộ luật Dân sự 2015` (điều + nhiều cấp)   | Resolve `BLDS_2015_D522`; gom đủ Phần 3 → Chương XVI → Mục 10 → Tiểu mục 1; citation `Điều 522 Tiểu mục 1 Mục 10 Chương XVI Phần thứ ba của Bộ luật Dân sự 2015` |
| `Điều 9999 ...` (G2 fail)                               | Fallback (Null) → `related_nodes=[]`, `related_documents=['BLDS_2015']`, không bịa                                                |
| `Quy định chung về hợp đồng ...` (không có document)    | Fallback → `extracted_hierarchy=null`, `node_information=null`, `related_nodes=[]`                                               |
| `Khoản 1 của Bộ luật Dân sự 2015` (G1 invalid: khoản ≠> điều) | Fallback → `related_nodes=[]`                                                                                                   |

Ghi chú:
- `citation` cho tổ tiên/đích đúng thứ tự **nhỏ → lớn** (ví dụ `Khoản 1 Điều 2 Chương I của Hiến pháp ...`).
- `label` suy từ label graph (ví dụ `SubSection`), `node_information.node_type` map `Subsection → SubSection`.
- `document_id` hiện diện trên mọi node trong `related_nodes` (đã sửa projection `get_ancestors`).
- Cảnh báo `effective_to does not exist` phát sinh từ `get_document_provenance` khi document không set property này (pre-existing, ngoài phạm vi V1).
