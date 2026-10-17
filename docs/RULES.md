# RULES — Quy ước code bắt buộc

> Đây là **hợp đồng chất lượng** của dự án. Agent/dev **bắt buộc** tuân thủ.
> Chỉ developer được sửa file này. Rules sẽ được bổ sung dần.
> Quy ước chung, mô tả dự án và quy trình agent: xem `AGENTS.md`.

Mỗi mục dưới đây là **một phạm vi riêng**, áp dụng độc lập. Vi phạm rule nào thì sửa theo đúng rule đó.

| # | Phạm vi | Áp dụng cho |
| - | ------- | ----------- |
| 1 | Kiến trúc & phân lớp | Toàn repo |
| 2 | Cấu hình | `src/**` |
| 3 | Hằng số / schema / tiện ích dùng chung | `src/**`, `scripts/**` |
| 4 | Logging | Mọi file `.py` nghiệp vụ |
| 5 | API | `src/api/**` |
| 6 | Docstring & style | Mọi file `.py` |
| 7 | Git | Toàn repo |
| 8 | Quy trình agent | Agent |

---

## 1. Kiến trúc & phân lớp

**Phạm vi:** toàn repo.

- **Toàn bộ logic nghiệp vụ nằm trong `src/`.**
- Client — FastAPI routes (`src/api/routes/*`), `scripts/**`, `notebooks/**` — **chỉ được *sử dụng* service, KHÔNG chứa business logic, KHÔNG tự wiring** hạ tầng.
- Khởi tạo/wiring service tập trung một chỗ: `src/common/container.py` → `build_services(settings)`.
- Service dùng chung khởi tạo **một lần** khi server start (`lifespan` trong `src/api/server.py`) và tái sử dụng cho mọi request.
- Route chỉ đọc service dùng chung từ `app.state` qua `src/api/dependencies.py`.

## 2. Cấu hình (Config-Driven)

**Phạm vi:** `src/**`.

- **CẤM `os.getenv` trong `src/`.** Dùng `get_settings()` từ `src/common/setting_config.py`.
- Thêm biến cấu hình mới = thêm field vào `Settings` (dùng `validation_alias` nếu tên env khác tên field). Không đọc env rải rác.
- CẤM hardcode hằng số/đường dẫn/ngưỡng/tên model trong code.

## 3. Hằng số, schema & tiện ích dùng chung

**Phạm vi:** `src/**`, `scripts/**`.

- Hằng số dùng chung: `src/common/constants.py` — `LegalLabels`, `LegalHierarchyLabels`, `LegalRelationshipTypes`, `MinimumScoreThresholds`, bảng La Mã & thứ tự tiếng Việt. **CẤM định nghĩa lại/nhân bản.**
- Schema/kiểu dùng chung: `src/common/schemas.py`. Lỗi nghiệp vụ: `src/common/custom_exception.py` (`CustomException`).
- Tiện ích: dùng lại `src/utils/*` (`file_utils`, `clean_text_utils`, `config_loader`, ...), **không viết lại**.

## 4. Logging

**Phạm vi:** mọi file `.py` nghiệp vụ.

- **BẮT BUỘC** dùng `setup_logger` trong `src/utils/logger.py`, khai báo ở cấp module, một lần/file:

  ```python
  from src.utils.logger import setup_logger

  logger = setup_logger("<module>", "<module>.log")
  ```

- Tham số dùng đúng như các file hiện có, ví dụ:
  `setup_logger("retrieval_service", filename="retrieval_service.log")`,
  `setup_logger("legal_model", "legal_model.log")`.
- **CẤM `import logging` và `logging.getLogger(...)`** trong code nghiệp vụ.
- **Ngoại lệ duy nhất:** chính `src/utils/logger.py`.

## 5. API

**Phạm vi:** `src/api/**`.

### 5.1. Envelope thống nhất

- Mọi endpoint trả về đúng **một trong hai shape** (`src/api/api_schemas.py`, helper `src/api/responses.py`):
  - Thành công — `SuccessResponse[T]`:

    ```json
    { "success": true, "status_code": 200, "message": "...", "result": { } }
    ```

  - Thất bại — `ErrorResponse`:

    ```json
    { "success": false, "status_code": 400, "message": "...", "path": "/api/...", "errors": ["..."] }
    ```

- **HTTP status code PHẢI bằng `status_code` trong body.**
- Route khai báo `response_model=ApiResponse[T]`; dữ liệu nghiệp vụ nằm trong `result`.
- Success **không** có `path`/`errors`; error **không** có `result`.
- **Mọi API** (kể cả `/health`) dùng envelope.

### 5.2. Xử lý lỗi

- Xử lý tập trung bằng **global exception handlers** (`register_exception_handlers` trong `src/api/server.py`).
- **CẤM try/except rải rác trong route** để tự format lỗi.
- Bắt cả exception Python lẫn `CustomException`, phân loại status code:

  | Exception | status_code |
  | --- | --- |
  | `CustomException` | `exc.status_code` |
  | `RequestValidationError` (sai schema) | 422 |
  | `StarletteHTTPException` (404/405...) | `exc.status_code` |
  | `ValueError` (validation input) | 400 |
  | `PermissionError` (auth) | 403 |
  | `Exception` (fallback) | 500 |

- Phân loại exception Python "thường" gom 3 nhóm: **auth** (`PermissionError` → 403), **validation input** (`ValueError` → 400), còn lại → **500**. Bảng ánh xạ nằm ở `CLASSIFIED_EXCEPTIONS` (`src/api/server.py`).
- **CẤM map `KeyError`, `TypeError`, `AttributeError`, `IndexError` → 4xx** (đó là bug nội bộ → 500).
- 5xx: **không lộ chi tiết/stacktrace ra client**, chỉ `message` chung; log đầy đủ (kèm traceback).
- Lỗi luôn trả `ErrorResponse` kèm `path`; `errors` là `list[str]`, không có `error_code`.

### 5.3. Route

- Route mỏng: validate input bằng schema → gọi service → wrap `SuccessResponse`. **Không business logic.**
- Lấy service qua `Depends` từ `src/api/dependencies.py`.
- Handler gọi service blocking nên viết `def` (đồng bộ) để FastAPI chạy trong threadpool; tránh `async def` gọi trực tiếp hàm blocking.

### 5.4. Middleware

- Đăng ký middleware tập trung tại `src/api/middlewares/registry.py` (`register_middlewares(app, settings)`). **CẤM rải `app.add_middleware` trong `server.py`/route.**
- Thêm middleware mới = thêm một lời gọi `app.add_middleware(...)` trong `register_middlewares`.
- Middleware áp cho **mọi request**; middleware log dùng `setup_logger` (không tự `import logging`).
- Thứ tự stack Starlette: middleware thêm **sau cùng** nằm **ngoài cùng** (chạy trước, kết thúc sau).

## 6. Docstring & style

**Phạm vi:** mọi file `.py`.

- **Mọi class và mọi method/hàm phải có docstring** (mục đích; thêm `Args`/`Returns`/`Raises` khi hữu ích) — style theo `src/graph/graph_repository.py`.
- Format: `black` line-length 88, `isort` profile black.
- Comment/tên biến tiếng Việt, giữ nhất quán. **Không thêm comment thừa vào code.**

## 7. Git

**Phạm vi:** toàn repo.

- **Không tự ý commit/push**; chỉ commit khi được yêu cầu.
- `.env` (chứa `NEO4J_PASSWORD`, `HF_TOKEN`) **không bao giờ commit**.
- Khi làm việc với scope `cicd`, ưu tiên tạo nhánh Git có prefix `cicd/` (ví dụ: `cicd/split-workflows`, `cicd/update-deploy-action`).

## 8. Quy trình agent

**Phạm vi:** agent.

- Lập plan `docs/plans/V{n}_{slug}.md` **trước khi code**; chia phase/subtask và đánh dấu tiến độ (xem `AGENTS.md`).

---

## 9. Tổng hợp vi phạm hiện tại

Danh sách ngắn các chỗ **chưa đúng rule** (cần chuyển đổi dần, không sửa gấp):

- **Rule 2 (Cấu hình):** `src/graph/neo4j_client.py` còn dùng `os.getenv` cho Neo4j.
- **Rule 4 (Logging):** còn `import logging` / `logging.getLogger` ở `src/graph/neo4j_client.py`, `src/graph/embedder.py`, `src/retrieval/semantic.py`.
- **Rule 1 (Kiến trúc):** một số module `src/retrieval/` còn rỗng (`graph_traverse.py`, `hybrid.py`).
