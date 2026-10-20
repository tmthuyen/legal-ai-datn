# V4 — Tích hợp Hệ thống: Services Golang & Frontend NextJS (Auth, Chat & AI Gateway)

> Trạng thái: **Hoàn thành** (Golang `services/`: 16 endpoint, build/vet/gofmt pass; Frontend triển khai ở V5)  
> Người thực hiện: subagents (Golang Subagent & Frontend Subagent)  
> Cập nhật: 2026-10-20  
> Next index theo PLAN_INDEX.md: `4`  
> Phạm vi: Xây dựng tầng `services/` (Golang + PostgreSQL) làm trung tâm Auth, Quản lý hội thoại & AI Gateway trung chuyển; đồng thời cấu hình và hoàn thiện `frontend/` (Next.js 16 + TailwindCSS v4 + Shadcn UI) làm giao diện hỏi đáp pháp lý, quản lý chat, tài khoản và admin quản trị. Tuyệt đối **không sửa đổi code logic hiện tại của `backend/` (FastAPI)**.

### Tài liệu nền tảng bắt buộc đọc trước khi code

| Tài liệu | Nội dung |
| -------- | -------- |
| `docs/architecture.md` | Kiến trúc 3 khối, ranh giới, luồng E2E, invariants |
| `docs/contracts/API_CONTRACT.md` | Hợp đồng endpoint/field/kiểu + DB schema + env (**nguồn sự thật duy nhất**) |
| `docs/RULES_SERVICES_FRONTEND.md` | Rule cứng cho 2 scope services/frontend |
| `docs/RULES.md` | Rule chung toàn repo |

### Quyết định đã chốt (2026-10-20)

- **Go stack:** Gin + GORM (`github.com/gin-gonic/gin`, `gorm.io/gorm`, `gorm.io/driver/postgres`).
- **Migration:** GORM `AutoMigrate` khi khởi động (dev). File `.env.example` đầy đủ.
- **Frontend cleanup:** **giữ** code phim cũ nhưng **không dùng để render**; không xóa.
- **Verification:** subagent tự chạy tĩnh — `go build/vet` và `npm run type-check/lint/build`. Không cần Postgres/Neo4j chạy sẵn; E2E để dev tự chạy.

---

## 1. Bối cảnh & Tầm nhìn kiến trúc (Architecture Overview)

Hệ thống Legal AI hoàn chỉnh gồm 3 khối độc lập nhưng giao tiếp thống nhất:

```
[ Frontend: Next.js (port 3002) ]
        │  ▲
        │  │  HTTP / REST (JWT accessToken Header + RefreshToken HttpOnly Cookie)
        ▼  │
[ Services: Golang Gin/Echo (port 8080) ] ── (PostgreSQL: Users, Roles, Conversations, Messages, AuditLogs)
        │  ▲
        │  │  Internal REST Client (POST /api/retrieval)
        ▼  │
[ Backend: FastAPI (port 8090) ] ── (Neo4j Knowledge Graph + Neo4j Vector Index + HuggingFace Embedding Model)
```

### Phân định trách nhiệm:
1. **Frontend (Next.js)**: Giao diện người dùng cho Landing Page Pháp luật, Đăng nhập/Đăng ký, Trang Chat hỏi đáp pháp luật thông minh (hiển thị trích dẫn, điều luật liên quan, breadcrumb), Quản lý lịch sử hội thoại, Cập nhật Profile và Dashboard Admin.
2. **Services (Golang)**: 
   - Đảm nhiệm nghiệp vụ cốt lõi: Auth (JWT, Refresh Token trong Cookie HttpOnly, Bcrypt), User, RBAC (Role: `admin`, `user`).
   - Quản lý Chat & Lịch sử hội thoại: tạo conversation, lưu message câu hỏi của user và câu trả lời kèm citations từ AI.
   - **AI Gateway**: Nhận prompt/câu hỏi từ Frontend, kiểm tra rate limit & session, chuyển tiếp request sang `backend:8090/api/retrieval`, nhận kết quả cấu trúc pháp lý, lưu trữ vào PostgreSQL và trả về cho Frontend.
3. **Backend (FastAPI)**: Giữ nguyên hiện trạng đóng vai trò Worker / AI Microservice chuyên sâu về Knowledge Graph Retrieval & Reasoning.

---

## 2. Quy ước Response Envelope chuẩn (Contract Agreement)

Để Server Golang và Client NextJS giao tiếp đồng nhất 100%, tất cả response từ Golang API **bắt buộc tuân thủ chuẩn Envelope**:

### 2.1. Phản hồi thành công (Success Response)
HTTP Status: `200` hoặc `201`
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Thao tác thành công",
  "result": { ... }
}
```
*Lưu ý:* Key `statusCode` (camelCase) khớp với `ApiResponse<T>` hiện có ở `frontend/src/shared/types/api.types.ts`.

### 2.2. Phản hồi có phân trang (Pagination Response)
HTTP Status: `200`
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Lấy danh sách thành công",
  "result": [ ... ],
  "pagination": {
    "total": 100,
    "page": 1,
    "limit": 20,
    "totalPages": 5
  }
}
```

### 2.3. Phản hồi lỗi (Error Response)
HTTP Status: `400`, `401`, `403`, `404`, `422`, `500`
```json
{
  "success": false,
  "statusCode": 400,
  "message": "Mô tả lỗi ngắn gọn cho người dùng",
  "errors": [
    "Chi tiết lỗi cụ thể nếu có"
  ]
}
```
*Nguyên tắc bất di bất dịch:* HTTP Status Code của header HTTP **phải luôn bằng `statusCode` trong JSON body**.

---

## 3. Database Schema Contract (PostgreSQL trong Golang)

Golang service sử dụng GORM (hoặc sqlx) kết nối PostgreSQL:

1. **`users`**:
   - `id` (UUID / varchar(36), PK)
   - `email` (varchar, unique, not null)
   - `username` (varchar, unique, not null)
   - `password_hash` (varchar, not null)
   - `full_name` (varchar)
   - `avatar_url` (varchar)
   - `role` (varchar: `user` | `admin`, default `user`)
   - `is_active` (boolean, default true)
   - `created_at`, `updated_at`
2. **`conversations`**:
   - `id` (UUID, PK)
   - `user_id` (UUID, FK -> users.id, not null)
   - `title` (varchar, default 'Cuộc trò chuyện mới')
   - `created_at`, `updated_at`
3. **`messages`**:
   - `id` (UUID, PK)
   - `conversation_id` (UUID, FK -> conversations.id, not null)
   - `sender` (varchar: `user` | `bot`, not null)
   - `content` (text, not null)
   - `extracted_hierarchy` (jsonb, nullable: cấu trúc luật AI trích xuất)
   - `related_nodes` (jsonb, nullable: các điều khoản, văn bản liên quan AI trả về)
   - `metadata` (jsonb, nullable: response time, model version)
   - `created_at`

---

## 4. API Endpoints Specification (Golang Services)

Prefix: `/api/v1`

### 4.1. Auth & Profile
- `POST /api/v1/auth/register`: Đăng ký tài khoản mới -> `{ accessToken, user }` + Cookie `refreshToken`.
- `POST /api/v1/auth/login`: Đăng nhập username/password -> `{ accessToken, user }` + Cookie `refreshToken`.
- `POST /api/v1/auth/refresh`: Đọc Cookie `refreshToken`, cấp lại `accessToken` mới.
- `POST /api/v1/auth/logout`: Xóa Cookie `refreshToken`.
- `GET /api/v1/auth/me`: Lấy thông tin user hiện tại qua `Bearer <accessToken>`.
- `PUT /api/v1/user/profile`: Cập nhật thông tin cá nhân (họ tên, avatar).
- `PUT /api/v1/user/password`: Đổi mật khẩu.

### 4.2. Chat & AI Gateway
- `GET /api/v1/chat/conversations`: Lấy danh sách cuộc hội thoại của user (phân trang).
- `POST /api/v1/chat/conversations`: Tạo cuộc hội thoại mới.
- `DELETE /api/v1/chat/conversations/:id`: Xóa cuộc hội thoại.
- `GET /api/v1/chat/conversations/:id/messages`: Lấy lịch sử tin nhắn của cuộc hội thoại.
- `POST /api/v1/chat/conversations/:id/messages`: Gửi câu hỏi pháp luật:
  1. Lưu message của user vào DB.
  2. Gọi `http://localhost:8090/api/retrieval` payload: `{"query_text": message.content}`.
  3. Nhận phản hồi `RetrievalResult`.
  4. Lưu message của bot (nội dung trả lời + trích dẫn `related_nodes` + `extracted_hierarchy`) vào DB.
  5. Trả về cả 2 message cho client.

### 4.3. Admin Management (Role `admin`)
- `GET /api/v1/admin/users`: Quản lý danh sách người dùng.
- `PUT /api/v1/admin/users/:id/status`: Khóa/mở khóa tài khoản.
- `GET /api/v1/admin/analytics`: Thống kê tổng số user, số hội thoại, số câu hỏi pháp luật đã truy vấn.

---

## 5. Phân công Subagents & Task Breakdown

### Subagent 1: Golang Services Engineer (`services/`)
* **Thư mục làm việc:** `services/`
* **Công nghệ:** Go 1.23+, **Gin**, **GORM (AutoMigrate)**, PostgreSQL, `golang-jwt/v5`, `golang.org/x/crypto/bcrypt`, `godotenv`.
* **Quy tắc bắt buộc:**
  - Cấu trúc clean architecture: `cmd/api/main.go`, `internal/config`, `internal/domain`, `internal/repository`, `internal/service`, `internal/handler`, `internal/middleware`, `internal/aiclient`, `pkg/response`, `pkg/jwt`, `pkg/hash`.
  - Mọi response dùng helper `response.Success/Paginated/Error`; không `c.JSON` rải rác.
  - Không hardcode URL/credentials; đọc từ `.env` qua `internal/config`.
  - HTTP Client gọi Backend `POST {AI_BACKEND_URL}/api/retrieval`, map envelope Backend (`status_code` snake_case) → `RetrievalResult`.
  - Tuân thủ `docs/RULES_SERVICES_FRONTEND.md` + `docs/contracts/API_CONTRACT.md`.
* **Phases:**
  | # | Phase | Nội dung | Trạng thái |
  | - | ----- | -------- | ---------- |
  | 1 | Scaffold | `go.mod`, `.env.example`, cấu trúc thư mục, `internal/config` | ✅ |
  | 2 | Domain & DB | `domain` entity + `repository` (GORM AutoMigrate: User, Conversation, Message) | ✅ |
  | 3 | Helpers | `pkg/response` (envelope), `pkg/jwt`, `pkg/hash` | ✅ |
  | 4 | Auth | service+handler: register, login, refresh, logout, me; middleware RequireAuth/RBAC; cookie refresh | ✅ |
  | 5 | User/Profile | profile, change password | ✅ |
  | 6 | Chat & AI Gateway | conversations CRUD, messages, `aiclient` gọi Backend, lưu bot message | ✅ |
  | 7 | Admin | list users, lock/unlock, analytics | ✅ |
  | 8 | Middleware & wiring | CORS, Recovery, Logger, router, `main.go` | ✅ |
  | 9 | Verify | `go mod tidy && go build ./... && go vet ./...` | ✅ (Go 1.23.5, build/vet/gofmt pass) |

### Subagent 2: Frontend NextJS Engineer (`frontend/`)
* **Thư mục làm việc:** `frontend/`
* **Công nghệ:** Next.js 16 (App Router), React 19, TypeScript, TailwindCSS v4, Shadcn UI, Zustand, TanStack Query, Axios.
* **Quy tắc bắt buộc:**
  - **Giữ** các file code phim cũ (không xóa), nhưng **không dùng để render** UI mới; chuyển trọng tâm sang Legal AI.
  - Tái sử dụng `axiosClient`, `useAuthStore`, shadcn/ui có sẵn.
  - Kiểu API khớp `docs/contracts/API_CONTRACT.md`; cấm `any`/`@ts-ignore`.
  - Tuân thủ `docs/RULES_SERVICES_FRONTEND.md`.
* **Phases:**
  | # | Phase | Nội dung | Trạng thái |
  | - | ----- | -------- | ---------- |
  | 1 | Config & types | `.env`/`.env.example` trỏ Services `:8080/api/v1`; types Legal AI; `app.config.ts` + metadata | ⬜ |
  | 2 | API layer | `src/apis/legal.api.ts` (auth/user/chat/admin) + hook TanStack Query | ⬜ |
  | 3 | Auth UI | Login/Register kết nối Services; bảo vệ route | ⬜ |
  | 4 | Landing | Landing page pháp luật (giới thiệu, tra cứu Hiến pháp & BLDS) | ⬜ |
  | 5 | Chat | Trang chat hỏi đáp + component trích dẫn (Điều/Khoản/Điểm, breadcrumb) | ⬜ |
  | 6 | Conversations | Danh sách/quản lý hội thoại | ⬜ |
  | 7 | Profile | Cập nhật profile + đổi mật khẩu | ⬜ |
  | 8 | Admin | Quản lý user + thống kê | ⬜ |
  | 9 | Verify | `npm install && npm run type-check && npm run lint && npm run build` | ⬜ |

---

## 6. Kế hoạch xác minh (Verification Plan)

1. **Khởi chạy độc lập:**
   - `services`: Chạy `go build ./...` và `go run cmd/api/main.go` -> kiểm tra port 8080 và route `/health`.
   - `frontend`: Chạy `npm run type-check`, `npm run lint` và `npm run build` không có lỗi.
2. **Kiểm thử tích hợp luồng nghiệp vụ E2E:**
   - Đăng ký tài khoản mới trên giao diện -> kiểm tra dữ liệu lưu vào PostgreSQL.
   - Đăng nhập -> nhận token -> truy cập trang cá nhân.
   - Gửi câu hỏi "Điều 1 Hiến pháp 2013 quy định gì?" trên giao diện Chat -> Golang service nhận -> chuyển tiếp sang FastAPI `backend:8090/api/retrieval` -> trả về kết quả kèm các điều khoản liên quan -> Frontend render đẹp mắt.
