# Kiến trúc Hệ thống Legal AI (3 khối)

> Trạng thái: **Chốt (baseline)**
> Người thực hiện: agent
> Cập nhật: 2026-10-20
> Phạm vi: Mô tả kiến trúc tổng thể của hệ thống Legal AI gồm 3 khối `frontend/`, `services/`, `backend/` và hợp đồng giao tiếp giữa chúng. Tài liệu này là **nguồn sự thật** cho mọi agent/dev khi tích hợp.

---

## 1. Sơ đồ tổng thể

```
[ Frontend: Next.js 16 — port 3003 ]
        │  ▲
        │  │  HTTP/REST  (Authorization: Bearer <accessToken>)
        │  │              (refreshToken: HttpOnly Cookie, withCredentials)
        ▼  │
[ Services: Golang + Gin — port 8080 ] ── (PostgreSQL: users, conversations, messages, ...)
        │  ▲
        │  │  Internal REST  (POST /api/retrieval, JSON)
        ▼  │
[ Backend: FastAPI — port 8090 ] ── (Neo4j Knowledge Graph + Embedding/Reasoning model)
```

| Khối | Thư mục | Cổng | Vai trò |
| ---- | ------- | ---- | ------- |
| Frontend | `frontend/` | 3003 | Giao diện người dùng (Next.js 16, App Router, Tailwind v4, shadcn/ui) |
| Services | `services/` | 8080 | Auth, User, RBAC, Chat/conversation, AI Gateway (Gin + GORM + PostgreSQL) |
| Backend | `backend/` | 8090 | AI Worker: Knowledge Graph Retrieval & Reasoning (FastAPI, **giữ nguyên, không sửa**) |

---

## 2. Ranh giới & trách nhiệm

### 2.1. Frontend (`frontend/`)
- Chỉ giao tiếp với **Services (Golang)**, không gọi trực tiếp Backend FastAPI.
- Auth: giữ `accessToken` trong bộ nhớ (Zustand, **không** localStorage); `refreshToken` do browser tự gửi qua HttpOnly cookie (`withCredentials: true`).
- Hiển thị: Landing pháp luật, Auth (login/register), Chat hỏi đáp luật (kèm trích dẫn Điều/Khoản/Điểm + breadcrumb), Quản lý hội thoại, Profile, Admin dashboard.

### 2.2. Services (`services/`)
- **Nguồn sự thật duy nhất** cho: người dùng, phiên đăng nhập, phân quyền, hội thoại, tin nhắn.
- **AI Gateway**: nhận câu hỏi → lưu message user → gọi `backend:8090/api/retrieval` → lưu message bot (kèm citations) → trả về cho Frontend.
- Không chứa logic suy luận pháp lý; chỉ trung chuyển + lưu trữ.

### 2.3. Backend (`backend/` FastAPI)
- **Đóng băng**: agent/dev **không được sửa** code logic trong `backend/` trong phạm vi V4.
- Hợp đồng đã biết: `POST /api/retrieval` body `{ "query_text": "..." }`, response envelope `{success, status_code, message, result}` với `result` gồm 6 key (xem §4.3).
- `GET /health` để kiểm tra sẵn sàng.

---

## 3. Luồng nghiệp vụ chính (E2E)

### 3.1. Đăng ký / Đăng nhập
1. Frontend `POST /api/v1/auth/register` (hoặc `/login`) qua `axiosClient`.
2. Services tạo/kiểm tra user, cấp `accessToken` (JWT, trong body) + set `refreshToken` (HttpOnly cookie).
3. Frontend lưu `accessToken` vào `useAuthStore`, gọi `GET /api/v1/auth/me` để lấy profile.

### 3.2. Refresh token khi 401
1. `axiosClient` response interceptor bắt `401` → gọi `POST /api/v1/auth/refresh` (cookie tự gửi).
2. Nhận `accessToken` mới → cập nhật store → retry request gốc.
3. Refresh thất bại → xóa token, coi như đăng xuất.

### 3.3. Hỏi đáp pháp luật
1. Frontend `POST /api/v1/chat/conversations/:id/messages` body `{ "content": "Điều 1 Hiến pháp 2013 quy định gì?" }`.
2. Services lưu message `sender=user`.
3. Services gọi `POST http://localhost:8090/api/retrieval` với `{ "query_text": content }`.
4. Nhận `result` (RetrievalResult) → Services lưu message `sender=bot` (nội dung trả lời + `extracted_hierarchy` + `related_nodes` + `metadata`).
5. Services trả về cả 2 message → Frontend render (kèm thẻ trích dẫn).

---

## 4. Hợp đồng giao tiếp (Contracts)

### 4.1. Envelope chuẩn (Services ↔ Frontend)
Mọi response của Services tuân thủ **một trong hai shape**. Chi tiết & ví dụ: `docs/contracts/API_CONTRACT.md`.

```jsonc
// Success
{ "success": true, "statusCode": 200, "message": "...", "result": { } }
// Error
{ "success": false, "statusCode": 400, "message": "...", "errors": ["..."] }
```

**Nguyên tắc bất di bất dịch:** HTTP status header **luôn bằng** `statusCode` trong body.

### 4.2. Envelope Backend FastAPI (đã tồn tại, không đổi)
```jsonc
{ "success": true, "status_code": 200, "message": "...", "result": { } }
{ "success": false, "status_code": 400, "message": "...", "path": "/api/retrieval", "errors": [] }
```
> Lưu ý: Backend dùng `status_code` (snake_case); Services dùng `statusCode` (camelCase). Services **phải** map đúng khi gọi nội bộ.

### 4.3. RetrievalResult (Backend `result`)
```jsonc
{
  "input": "câu hỏi gốc",
  "extracted_hierarchy": { /* phân cấp luật parse được, hoặc {} */ },
  "node_information": null,      // hoặc dict
  "related_documents": [ /* ... */ ],
  "related_nodes": [ /* node liên quan: node_id, type, title, number, text, citation... */ ],
  "relationships": [ /* ... */ ]
}
```
Services **không được bịa** key ngoài danh sách trên.

### 4.4. DB Schema (PostgreSQL — Services)
Chi tiết cột + kiểu: `docs/contracts/API_CONTRACT.md` §DB. Bảng: `users`, `conversations`, `messages`.

---

## 5. Nguyên tắc bất biến (Invariants)

1. **Không sửa `backend/`** trong phạm vi V4.
2. **Không hardcode** URL/credentials/secret: đọc từ biến môi trường (`.env`).
3. **Không bịa** endpoint, field, kiểu dữ liệu — chỉ dùng những gì ghi trong `docs/contracts/API_CONTRACT.md`.
4. Envelope & `statusCode == HTTP status` áp cho **mọi** endpoint Services.
5. Frontend **không** gọi trực tiếp Backend FastAPI.
