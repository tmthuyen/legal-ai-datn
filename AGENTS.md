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

## Trạng thái code: một số module còn RỖNG (0 byte)

Module còn rỗng (không kể `__init__.py`):

- `src/main.py`
- `src/reasoning/{condition_checker,extractor,generator,syllogism}.py`
- `src/verification/{confidence,counterfactual,nli}.py`
- `src/eval/{dataset_eval,metrics_eval,runner_eval}.py`
- `src/retrieval/{graph_traverse,hybrid}.py`

`graph_traverse.py`/`hybrid.py` còn rỗng → luồng traversal/hybrid hiện nằm trong `src/retrieval/retrieval_service.py`.

Đã triển khai thật:

- Data/graph: `graph/import_neo4j.py`, `src/graph/{neo4j_client,graph_repository,graph_service,embedder}.py`.
- Retrieval: `src/retrieval/{legal_query_extractor,semantic,retrieval_service}.py`.
- API: `src/api/{server,api_schemas,dependencies}.py` + `src/api/routes/{health,retrieval}.py` → `uvicorn src.api.server:app` **chạy được** (cần Neo4j đang bật).
- Chung/tiện ích: `src/common/*` (gồm `container.py`), `src/models/legal_model.py`, `src/utils/*`.
- Script: `scripts/{embed_nodes,test_graph,test_retrieval,run_ablation_experiments}.py`.

- **Không có test suite pytest** (dù `pytest` có trong dev deps). `scripts/test_*.py` là script thủ công, không phải pytest.
- Tên đúng là `src/retrieval/legal_query_extractor.py` (README ghi sai là `legal_query.py`).
- `scripts/seed_graph.py`, `eval_pipeline.py`, `test_reasoning.py`, `test_models.py` **không tồn tại** (README nhắc tới nhưng chưa có).

## Đặc điểm đồ thị/dữ liệu (dễ sai)

- **`type` KHÔNG phải property trên node.** `graph/import_neo4j.py` loại bỏ key `type` khi import (`k != 'type'`); loại node chỉ tồn tại dưới dạng label `:LegalNode:<Type>`. Vì vậy mọi truy vấn/code dùng `n.type` trả về null — dùng `labels(n)` rồi bỏ `LegalNode`. Các chỗ còn lỗi: `graph_repository.py:781` (`count_nodes_by_type`), `graph_repository.py:449` (`get_ancestors`), `graph_service.py` (`content.type` trong `get_full_retrieval_context`).
- **`node_id` không tái tạo được từ số hiển thị.** Chapter đánh số **tuần tự** (`_CH1`), KHÔNG theo số La Mã (Chương II → `..._P1_CH2`). Luôn resolve qua đồ thị, đừng build chuỗi.
  - `Document={DOC}`, `Part={DOC}_P{n}`, `Chapter={DOC}[_P{p}]_CH{n}`, `Section={DOC}_CH{ch}_M{n}`, `SubSection={DOC}_CH{ch}_M{m}_TM{n}`, `Article={DOC}_D{n}`, `Clause={DOC}_D{d}_K{k}`, `Point={DOC}_D{d}[_K{k}]_DIEM_{A}` (chữ hoa, có tiền tố `DIEM_`).
- **Kiểu `number` không nhất quán**: `Article`/`Clause` là `int`; `Chapter`/`Section`/`SubSection`/`Point`/`Part` là `str`. Cần chuẩn hoá khi so khớp (`src/common/constants.py` có bảng La Mã & thứ tự tiếng Việt).
- **Nội dung Article nằm ở `full_text`**, không phải `text` (`text` chỉ là đoạn mở đầu Điều). Chỉ Article có `full_text`; các loại khác không.
- Relation whitelist: `CONTAINS, REFERENCES, IMPLEMENTS, INTERPRETED_BY, AMENDS, REPEALS, REPLACED_BY, RELATED_TO`. Quan hệ cấu trúc là `CONTAINS` (parent → child).
- Quy mô hiện tại: **3,472 nodes / 3,959 relations** (CONTAINS 3467, REFERENCES 489, IMPLEMENTS 2, INTERPRETED_BY 1).
- Embedding: Article + `darklethelong/vnlegal-lal` (1024-d, cosine, Context-Enriched), vector index `article_embeddings_idx` trên Neo4j.

## Cấu hình & dữ liệu (Config-Driven)

- `backend/data/documents_config.json` — danh mục văn bản + metadata + aliases + relations khai báo.
- `backend/data/parser_profiles.json` — regex nhận diện cấu trúc theo loại văn bản (`default`, `nghi_dinh`, `nghi_quyet`).
- Thêm loại văn bản mới = thêm profile + config, **không sửa code parser**.
- Output notebook 02 → `backend/data/processed/{nodes,relations,unresolved_references,unresolved_document_relations}.json`.
- `backend/data/van_ban/` (file `.docx` nguồn) **bị gitignore** — có thể không có sẵn, nên notebook 01 có thể không chạy lại được.

## Quy ước code & git

Dưới đây là quy ước chung cơ bản. Chi tiết các quy ước code (RULES) và các rule bắt buộc nằm trong `docs/RULES.md` — file đó chỉ được đọc, nếu sửa phải có developer yêu cầu (developer có thể tự sửa file đó).

- **Mọi hàm/method viết trong class Python phải có docstring mô tả rõ ràng** (mục đích; thêm `Args`/`Returns` khi hữu ích) — theo style hiện có ở `src/graph/graph_repository.py`.
- Format: `black` line-length 88, `isort` profile black. Comment/tên biến dùng tiếng Việt — giữ nhất quán.
- Không thêm comment vào code trừ khi được yêu cầu.
- `.env` chứa `NEO4J_PASSWORD`/`HF_TOKEN` — **không bao giờ commit**. `.gitignore` bỏ qua `.env`, `.agents/`, `logs`, `**/data/van_ban/`.
- Không tự ý commit/push; chỉ commit khi được yêu cầu.

## RULES bắt buộc (chi tiết: `docs/RULES.md`)

Các rule cứng, agent/dev **phải tuân thủ**. Chi tiết đầy đủ và danh sách vi phạm hiện tại nằm trong `docs/RULES.md`. Tóm tắt:

- **Kiến trúc:** logic nghiệp vụ chỉ nằm trong `src/`; routes/`scripts/**`/notebook chỉ *sử dụng* service (không viết logic, không tự wiring). Wiring tập trung ở `src/common/container.py`.
- **Config:** cấm `os.getenv` trong `src/` — dùng `get_settings()` (`src/common/setting_config.py`).
- **Dùng chung:** tái sử dụng `src/common/constants.py`, `src/common/schemas.py`, `src/common/custom_exception.py` và `src/utils/*`; cấm nhân bản hằng số/logic.
- **Logging:** cấm `import logging`/`logging.getLogger`; bắt buộc `setup_logger` trong `src/utils/logger.py` (vd `setup_logger("retrieval_service", "retrieval_service.log")`). Ngoại lệ: chính `logger.py`.
- **API:** mọi endpoint trả envelope `SuccessResponse[T]` / `ErrorResponse` (`src/api/api_schemas.py`); **HTTP status = `status_code` trong body**; xử lý lỗi tập trung bằng global exception handlers; 5xx không lộ chi tiết nội bộ; middleware đăng ký tập trung ở `src/api/middlewares/registry.py`.

## Quy trình của agent

- Khi nhận task/yêu cầu, agent **phải lập plan và lưu vào docs/plans/** trước khi triển khai.
  - Đặt tên file plan theo định dạng: V{index}_{scope}_{task_name}.md
    - {index}: số thứ tự liên tục (integer), bắt đầu từ 0. Xác định dựa trên toàn bộ plans trong docs/plans/ (xem docs/plans/PLAN_INDEX.md).
    - {scope}: ∈ ackend | rontend | cicd | i
    - {task_name}: slug dạng kebab-case (lowercase, dùng - thay khoảng trắng), mô tả ngắn gọn công việc.
    - VD: V0_init-plan.md, V1_cicd_ci-cd-split-workflows.md, V2_backend_retrieval-target-validation.md, V3_backend_retrieval-api.md
  - Tiêu đề trong file: # V{index} — <mô tả>
  - Ghi đầy đủ: trạng thái, người thực hiện & thời gian thực hiện, các module được sửa hoặc liên quan, phạm vi (theo mẫu docs/plans/V1_retrieval_target_validation.md).
  - Khi tạo plan mới, **bắt buộc cập nhật docs/plans/PLAN_INDEX.md** (mapping file↔index↔scope↔task_name↔mô tả, 
ext_index = max(index)+1).
  - Nếu phát hiện sai số thứ tự (trùng lặp, không liên tục), đề xuất sắp xếp lại tên file theo thứ tự hợp lý — **chỉ thực hiện rename sau khi có xác nhận từ người dùng**, đồng thời cập nhật PLAN_INDEX.md tương ứng.

- Các task trong plan phải mô tả rõ ràng
- Khi làm việc với scope `cicd`, ưu tiên tạo nhánh Git có prefix `cicd/` (ví dụ: `cicd/split-workflows`, `cicd/update-deploy-action`). và chia nhỏ thành phase hay subtask viết rõ trong plan đó để thực hiện. Đánh dấu tiến độ đã hoàn thành hay chưa
## Tài liệu tham chiếu

### Summary

Đây là các tài liệu tóm tắt, không phải hướng dẫn triển khai. Agent **không được sửa** các file này, chỉ đọc để hiểu quy trình & quy ước. Thêm mới khi có yêu cầu summamry cho các thay đổi code mới nhưng **không có** tài liệu mô tả.

- `docs/summary/DocumentParser_TransfromGraphNode.md` — quy tắc parse, quy ước `node_id`, quan hệ, validator V1–V9.

### Plans

Đây là các tài liệu mô tả kế hoạch triển khai, **agent được phép sửa** khi có yêu cầu. Thêm mới khi có task mới. Quản lý tên file theo `V{index}_{scope}_{task_name}.md` với `scope` ∈ `backend` | `frontend` | `cicd` | `ai`. Index là số thứ tự liên tục (0,1,...). Tiêu đề `# V{index} — <mô tả>`. Phải cập nhật `docs/plans/PLAN_INDEX.md` khi thêm/sửa/đổi tên. Xem chi tiết tại mục "Quy trình của agent".

- `docs/plans/V1_retrieval_target_validation.md` — pipeline retrieval + format JSON đầu ra (`input, extracted_hierarchy, related_documents, related_nodes`).

### Subtasks

- `docs/Subtask_Fine-tuning.md` — model nền `ntphuc149/ViLegalQwen2.5-1.5B-Base`, task LegalQRHE.

### Docs cho backend

Mô tả chi tiết các thao tác trong backend để agent hoặc dev tự thực hiện

- `backend/docs/CHAY_TRONG_VENV.md`, `backend/docs/CAU_TRUC_DU_AN_BAN_DAU.md` — hướng dẫn chạy & cấu trúc dự kiến.
