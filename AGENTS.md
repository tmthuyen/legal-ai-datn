# AGENTS.md

Hướng dẫn chung cho AI coding agent khi làm việc trong repo này. Đọc các tài liệu gốc trong `docs/` và `backend/docs/` trước khi tin README (README mô tả cấu trúc _dự kiến_, không phải hiện trạng).

## Dự án

- Các mô tả tổng quát dự án nằm trong `README.md`. Mô tả về dự án, công nghệ, cấu trúc thư mục, cách chạy lệnh, các tài liệu và file _.md_ tham chiếu.
- Đồ án: **Legal AI — Knowledge Graph & Counterfactual Reasoning**. Hệ thống GraphRAG trợ đáp pháp lý Việt Nam.
- Corpus giới hạn **5 văn bản**: `HIEN_PHAP_2013`,
  `BLDS_2015`, `ND_21_2021`, `ND_19_2019`, `NQ_02_2022`.
- Đồ thị phân cấp: `Document → Part → Chapter → Section → SubSection → Article → Clause → Point`.
- **Toàn bộ code nằm trong `backend/`**. Chạy mọi lệnh Python/script từ thư mục `backend/`. Repo root chỉ có `README.md`, `docs/`, `backend/`.

## Chạy lệnh (luôn đứng ở `backend/`)

- Môi trường ảo: `backend\.venv` (đã cài editable → `import src...` mới hoạt động).
  - `.\.venv\Scripts\activate`
  - Cài lại: `pip install -e .` (thêm dev tools: `pip install -e ".[dev]"`)
- Windows + in tiếng Việt ra console: đặt `$env:PYTHONIOENCODING="utf-8"` trước khi chạy, tránh `UnicodeEncodeError` (cp1252).
- Cần Neo4j 5 đang chạy sẵn; cấu hình kết nối qua `backend/.env`.
- Nạp đồ thị: `python graph/import_neo4j.py` (cờ `--clear-db`, `--batch-size`).
- Sinh embedding Article: `python scripts/embed_nodes.py` (cờ `--use-cache`, `--index-only`, `--dry-run`, `--sample`).
- Smoke test kết nối/truy vấn: `python scripts/test_graph.py`.
- Notebook: chạy với cwd = `backend/notebooks`, đường dẫn trong notebook là `../data/...`. Thứ tự pipeline: `01_parse_data` → `02_transform` → `03_explore_graph` → `04_retrieval` → `05_*`.

## Trạng thái code: nhiều module còn RỖNG (0 byte)

Các lệnh trong README dưới đây **chưa chạy được** vì file rỗng:

- `src/api/*` (gồm `server.py`) và `src/main.py` → `uvicorn src.api.server:app` KHÔNG chạy.
- `src/reasoning/*`, `src/verification/*`, `src/eval/*`.
- `src/retrieval/semantic.py`, `graph_traverse.py`, `hybrid.py`, `reranker.py`.
- `scripts/seed_graph.py`, `eval_pipeline.py`, `test_retrieval.py`, `test_reasoning.py`, `test_models.py`; `notebooks/10_test_models.ipynb`.

Đã triển khai thật: `graph/import_neo4j.py`, `scripts/embed_nodes.py`, `scripts/test_graph.py`, `src/common/*`, `src/graph/{neo4j_client,graph_repository,graph_service,embedder}.py`, `src/retrieval/legal_query_extractor.py`, `src/utils/*`.

- **Không có test suite pytest** (dù `pytest` có trong dev deps). `scripts/test_*.py` là script thủ công, không phải pytest.
- Tên đúng là `src/retrieval/legal_query_extractor.py` (README ghi sai là `legal_query.py`).

## Đặc điểm đồ thị/dữ liệu (dễ sai)

- **`type` KHÔNG phải property trên node.** `graph/import_neo4j.py` loại bỏ key `type` khi import (`k != 'type'`); loại node chỉ tồn tại dưới dạng label `:LegalNode:<Type>`. Vì vậy mọi truy vấn/code dùng `n.type` trả về null — dùng `labels(n)` rồi bỏ `LegalNode`. Các chỗ còn lỗi: `graph_repository.py:781` (`count_nodes_by_type`), `graph_repository.py:449` (`get_ancestors`), `graph_service.py` (`content.type` trong `get_full_retrieval_context`).
- **`node_id` không tái tạo được từ số hiển thị.** Chapter đánh số **tuần tự** (`_CH1`), KHÔNG theo số La Mã (Chương II → `..._P1_CH2`). Luôn resolve qua đồ thị, đừng build chuỗi.
  - `Document={DOC}`, `Part={DOC}_P{n}`, `Chapter={DOC}[_P{p}]_CH{n}`, `Section={DOC}_CH{ch}_M{n}`, `SubSection={DOC}_CH{ch}_M{m}_TM{n}`, `Article={DOC}_D{n}`, `Clause={DOC}_D{d}_K{k}`, `Point={DOC}_D{d}[_K{k}]_DIEM_{A}` (chữ hoa, có tiền tố `DIEM_`).
- **Kiểu `number` không nhất quán**: `Article`/`Clause` là `int`; `Chapter`/`Section`/`SubSection`/`Point`/`Part` là `str`. Cần chuẩn hoá khi so khớp (`src/common/constants.py` có bảng La Mã & thứ tự tiếng Việt).
- **Nội dung Article nằm ở `full_text`**, không phải `text` (`text` chỉ là đoạn mở đầu Điều). Chỉ Article có `full_text`; các loại khác không.
- Relation whitelist: `CONTAINS, REFERENCES, IMPLEMENTS, INTERPRETED_BY, AMENDS, REPEALS, REPLACED_BY, RELATED_TO`. Quan hệ cấu trúc là `CONTAINS` (parent → child).
- Quy mô hiện tại: **3,472 nodes / 3,959 relations** (CONTAINS 3467, REFERENCES 489, IMPLEMENTS 2, INTERPRETED_BY 1).
- Embedding: Article + `BAAI/bge-m3` (1024-d, cosine), vector index `article_embeddings_idx`.

## Cấu hình & dữ liệu (Config-Driven)

- `backend/data/documents_config.json` — danh mục văn bản + metadata + aliases + relations khai báo.
- `backend/data/parser_profiles.json` — regex nhận diện cấu trúc theo loại văn bản (`default`, `nghi_dinh`, `nghi_quyet`).
- Thêm loại văn bản mới = thêm profile + config, **không sửa code parser**.
- Output notebook 02 → `backend/data/processed/{nodes,relations,unresolved_references,unresolved_document_relations}.json`.
- `backend/data/van_ban/` (file `.docx` nguồn) **bị gitignore** — có thể không có sẵn, nên notebook 01 có thể không chạy lại được.

## Quy ước code & git

Dưới đây là quy ước chung cơ bản. Chi tiết các quy ước code (RULES) nằm trong `docs/RULES.md`, file này chỉ đươc đọc, nếu sửa phải có developer yêu cầu và developer có thể tự sửa file này.

- **Mọi hàm/method viết trong class Python phải có docstring mô tả rõ ràng** (mục đích; thêm `Args`/`Returns` khi hữu ích) — theo style hiện có ở `src/graph/graph_repository.py`.
- Format: `black` line-length 88, `isort` profile black. Comment/tên biến dùng tiếng Việt — giữ nhất quán.
- Không thêm comment vào code trừ khi được yêu cầu.
- `.env` chứa `NEO4J_PASSWORD`/`HF_TOKEN` — **không bao giờ commit**. `.gitignore` bỏ qua `.env`, `.agents/`, `logs`, `**/data/van_ban/`.
- Không tự ý commit/push; chỉ commit khi được yêu cầu.

## Quy trình của agent

- Khi nhận task/yêu cầu, agent **phải lập plan và lưu vào `docs/plans/`** trước khi triển khai.
  - Đặt tên theo version: `V{n}_{slug}.md` (V1, V2, … Vn),
  - tiêu đề `# V{n} — <mô tả>`,
  - ghi trạng thái,
  - người thực hiện & thời gian thực hiện,
  - Các module được sửa hoăc liên quan,
  - phạm vi — theo mẫu `docs/plans/V1_retrieval_target_validation.md`.

- Các task trong plan phải mô tả rõ ràng và chia nhỏ thành phase hay subtask viết rõ trong plan đó để thực hiện. Đánh dấu tiến độ đã hoàn thành hay chưa

## Tài liệu tham chiếu

### Summary

Đây là các tài liệu tóm tắt, không phải hướng dẫn triển khai. Agent **không được sửa** các file này, chỉ đọc để hiểu quy trình & quy ước. Thêm mới khi có yêu cầu summamry cho các thay đổi code mới nhưng **không có** tài liệu mô tả.

- `docs/summary/DocumentParser_TransfromGraphNode.md` — quy tắc parse, quy ước `node_id`, quan hệ, validator V1–V9.

### Plans

Đây là các tài liệu mô tả kế hoạch triển khai, **agent được phép sửa** khi có yêu cầu. Thêm mới khi có task mới. Quản lý phiên bản và tên plan theo quy ước `V{n}_{slug}.md` (V1, V2, … Vn). Tiêu đề `# V{n} — <mô tả>`; ghi trạng thái, người thực hiện, phạm vi.

- `docs/plans/V1_retrieval_target_validation.md` — pipeline retrieval + format JSON đầu ra (`input, extracted_hierarchy, related_documents, related_nodes`).

### Subtasks

- `docs/Subtask_Fine-tuning.md` — model nền `ntphuc149/ViLegalQwen2.5-1.5B-Base`, task LegalQRHE.

### Docs cho backend

Mô tả chi tiết các thao tác trong backend để agent hoặc dev tự thực hiện

- `backend/docs/CHAY_TRONG_VENV.md`, `backend/docs/CAU_TRUC_DU_AN_BAN_DAU.md` — hướng dẫn chạy & cấu trúc dự kiến.
