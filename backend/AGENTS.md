# AGENTS.md (backend)

Hướng dẫn chi tiết nằm ở `../AGENTS.md` (repo root) — đọc file đó trước.

Nhắc nhanh khi làm việc trong `backend/`:

- Chạy mọi lệnh Python/script từ thư mục `backend/`; venv tại `backend\.venv` (đã cài editable nên `import src...` hoạt động).
- Windows: đặt `$env:PYTHONIOENCODING="utf-8"` trước khi chạy để tránh lỗi in tiếng Việt.
- Neo4j dùng `bolt://localhost:7687` (không dùng `neo4j://` cho instance đơn).
- Notebook chạy với cwd = `backend/notebooks`, đường dẫn là `../data/...`.
- Nhiều module còn rỗng (0 byte): xem mục "Trạng thái code" trong `../AGENTS.md` trước khi chạy lệnh theo README.
