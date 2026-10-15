# V2 — FastAPI server cho Retrieval (state dùng chung + config-driven)

> Trạng thái: **Hoàn thành (V2)**
> Người thực hiện: agent
> Cập nhật: 2026-10-15
> Module liên quan: `src/api/{server,api_schemas,responses,dependencies}.py`, `src/api/middlewares/*`, `src/api/routes/{health,retrieval}.py`, `src/common/{container,setting_config}.py`, `scripts/test_retrieval.py`
> Phạm vi: Dựng lớp API tối thiểu để kiểm thử truy vấn Retrieval. Nạp model + khởi tạo service dùng chung **một lần** khi server start, lưu vào `app.state` để tái sử dụng cho mọi request. Đọc cấu hình qua `get_settings()` thay cho `os.getenv`.

---

## 1. Mục tiêu

1. Viết `src/api/server.py`: FastAPI app + `lifespan` nạp model và khởi tạo service dùng chung, lưu vào `app.state.services`.
2. Cung cấp 2 API:
   - `GET /health` — kiểm tra trạng thái app + service + kết nối Neo4j.
   - `POST /api/retrieval` — nhận `query_text`, trả kết quả pipeline Retrieval V1 (6 key).
3. Toàn bộ cấu hình lấy từ `get_settings()` (`src/common/setting_config.py`), không dùng `os.getenv` trong tầng service/API.
4. Tách composition root ra `src/common/container.py` để cả API và script dùng lại (client chỉ *sử dụng*, không tự wiring nghiệp vụ).

---

## 2. Nguyên tắc

- **Model nạp 1 lần**: `lifespan` build service (kể cả load embedding + reasoning model) và lưu vào `app.state`; request chỉ đọc lại.
- **Không dead code / không tham số thừa**: request model chỉ chứa trường thực sự dùng.
- **Config-driven**: mọi tham số (Neo4j, embedding, model HF) đến từ `Settings`.
- Tuân thủ RULES: mọi hàm/class có docstring; comment/tên biến tiếng Việt; `black` line-length 88.

---

## 3. Phase & tiến độ

| # | Phase | Nội dung | Trạng thái |
| - | ----- | -------- | ---------- |
| 1 | Config | Bổ sung `hf_base_model`, `hf_model_id`, `hf_revision` vào `Settings` (alias `REVISION`) | ✅ |
| 2 | Container | `src/common/container.py`: `AppServices` + `build_services(settings)` | ✅ |
| 3 | Schema | `src/api/api_schemas.py`: `RetrievalRequest`, `RetrievalResponse`, `HealthResponse` | ✅ |
| 4 | DI | `src/api/dependencies.py`: lấy service từ `request.app.state` | ✅ |
| 5 | Routes | `routes/health.py` (`GET /health`), `routes/retrieval.py` (`POST /api/retrieval`) | ✅ |
| 6 | Server | `src/api/server.py`: `create_app()` + `lifespan` + CORS + handler `CustomException` | ✅ |
| 7 | Client | `scripts/test_retrieval.py` dùng `build_services` (bỏ wiring trùng lặp) | ✅ |
| 8 | Verify | `py_compile` + import-check `src.api.server` | ✅ |
| 9 | Envelope | `src/api/api_schemas.py`: `SuccessResponse[T]`/`ErrorResponse`/`ApiResponse[T]` + `src/api/responses.py` | ✅ |
| 10 | Exception | `src/api/server.py`: handler tập trung (CustomException/auth/validation/500) | ✅ |
| 11 | Verify | Stub smoke test 12 case (200/400/403/404/422/500), HTTP status = body `status_code` | ✅ |
| 12 | Middleware | `src/api/middlewares/`: registry tập trung + `RequestLoggingMiddleware` (response time, tên req, IP, user-agent, url) | ✅ |

---

## 4. Hợp đồng API

Mọi endpoint trả envelope chuẩn (xem `docs/RULES.md` mục 5); **HTTP status luôn bằng `status_code` trong body**.

### `GET /health` — 200

```json
{
  "success": true,
  "status_code": 200,
  "message": "Hệ thống hoạt động bình thường",
  "result": {
    "status": "ok",
    "app_name": "legal-ai",
    "app_version": "0.1.0",
    "services_ready": true,
    "neo4j_connected": true
  }
}
```

### `POST /api/retrieval` — 200

Request:

```json
{ "query_text": "Điều 522 của Bộ luật Dân sự 2015 quy định về vấn đề gì?" }
```

`result` gồm 6 key theo đặc tả V1 — `input`, `extracted_hierarchy`, `node_information`, `related_documents`, `related_nodes`, `relationships`.

### Lỗi (mọi endpoint)

```json
{
  "success": false,
  "status_code": 400,
  "message": "Dữ liệu đầu vào không hợp lệ",
  "path": "/api/retrieval",
  "errors": ["..."]
}
```

| Tình huống | status_code |
| ---------- | ----------- |
| `CustomException` | theo `status_code` của exception |
| Body/query sai schema (`RequestValidationError`) | 422 |
| `ValueError` (validation input) | 400 |
| `PermissionError` (auth) | 403 |
| `HTTPException` của Starlette (404/405...) | theo status hiện có |
| Không lường trước | 500 (không lộ nội bộ) |

---

## 5. Cách chạy

```powershell
# Từ backend/
$env:PYTHONIOENCODING="utf-8"
.\.venv\Scripts\python.exe -m uvicorn src.api.server:app --host 0.0.0.0 --port 8090
```

---

## 6. Ghi chú

- Nạp model reasoning (Qwen + PEFT) + embedding model ở startup tốn RAM/thời gian → `GET /health` dùng để chờ server sẵn sàng.
- Middleware `RequestLoggingMiddleware` ghi `method url | name | status | ms | ip | ua [ | error]`, dùng `setup_logger("request_logging", "request_logging.log")`.
- Chưa có: auth, rate-limit, streaming, persist log request. Để giai đoạn sau.
- Port mặc định lấy từ `settings.app_port` (8090) nếu chạy qua entrypoint; khi dùng `uvicorn` CLI thì truyền `--port`.
