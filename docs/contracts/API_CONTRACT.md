# API Contract — Legal AI (Services ↔ Frontend)

> Trạng thái: **Chốt (v1)**
> Cập nhật: 2026-10-20
> Phạm vi: Hợp đồng giao tiếp chính thức giữa **Services (Golang)** và **Frontend (Next.js)**.
> **Nguồn sự thật duy nhất** cho endpoint, field, kiểu dữ liệu. Agent/dev **cấm bịa** khác tài liệu này.
> Base URL: `http://localhost:8080` • Prefix: `/api/v1`

---

## 1. Quy ước chung

- Tất cả response là JSON, tuân thủ envelope ở §2.
- **HTTP status = `statusCode` trong body** (không được lệch).
- Auth: header `Authorization: Bearer <accessToken>` cho endpoint cần đăng nhập.
- Refresh token nằm trong cookie `refreshToken` (HttpOnly, SameSite=Lax, Path=/).
- Mọi thời gian là ISO-8601 UTC (`2026-10-20T10:00:00Z`).
- Mọi `id` là UUID v4 dạng chuỗi.

---

## 2. Envelope

### 2.1. Success
```json
{ "success": true, "statusCode": 200, "message": "Thao tác thành công", "result": { } }
```

### 2.2. Paginated
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Lấy danh sách thành công",
  "result": [ ],
  "pagination": { "total": 100, "page": 1, "limit": 20, "totalPages": 5 }
}
```

### 2.3. Error
```json
{ "success": false, "statusCode": 400, "message": "Mô tả lỗi ngắn gọn", "errors": ["chi tiết"] }
```

### 2.4. Bảng mã lỗi
| statusCode | Khi nào |
| ---------- | ------- |
| 400 | Input sai (business validation) |
| 401 | Thiếu/sai/hết hạn access token |
| 403 | Không đủ quyền (RBAC) |
| 404 | Không tìm thấy tài nguyên |
| 409 | Trùng lặp (email/username đã tồn tại) |
| 422 | Body sai schema (validate request) |
| 500 | Lỗi hệ thống (không lộ chi tiết nội bộ) |

---

## 3. Kiểu dữ liệu dùng chung

### 3.1. User
```ts
interface User {
  id: string;
  email: string;
  username: string;
  fullName: string | null;
  avatarUrl: string | null;
  role: 'user' | 'admin';
  isActive: boolean;
  createdAt: string; // ISO-8601
  updatedAt: string; // ISO-8601
}
```
> **Không** trả `passwordHash` trong bất kỳ response nào.

### 3.2. AuthResult
```ts
interface AuthResult {
  accessToken: string;
  user: User;
}
```

### 3.3. Conversation
```ts
interface Conversation {
  id: string;
  userId: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}
```

### 3.4. Message
```ts
interface Message {
  id: string;
  conversationId: string;
  sender: 'user' | 'bot';
  content: string;
  extractedHierarchy: Record<string, unknown> | null;
  relatedNodes: unknown[] | null;
  metadata: Record<string, unknown> | null;
  createdAt: string;
}
```

### 3.5. ChatReply (kết quả 1 lượt hỏi đáp)
```ts
interface ChatReply {
  userMessage: Message;   // message vừa lưu của user
  botMessage: Message;    // message bot kèm citations trong relatedNodes/extractedHierarchy
}
```

---

## 4. Endpoints

### 4.1. Auth

#### `POST /api/v1/auth/register` — 201
Request:
```json
{ "email": "a@b.com", "username": "alice", "password": "Secret123", "fullName": "Alice" }
```
- `email`: bắt buộc, email hợp lệ, unique
- `username`: bắt buộc, 3–50 ký tự, unique
- `password`: bắt buộc, tối thiểu 8 ký tự
- `fullName`: tùy chọn

Response `result`: `AuthResult`. Đồng thời set cookie `refreshToken`.
Lỗi: `409` nếu email/username đã tồn tại, `422` nếu sai schema.

#### `POST /api/v1/auth/login` — 200
Request:
```json
{ "username": "alice", "password": "Secret123" }
```
Response `result`: `AuthResult` + set cookie `refreshToken`.
Lỗi: `401` nếu sai thông tin.

#### `POST /api/v1/auth/refresh` — 200
Không body. Đọc cookie `refreshToken`.
Response `result`: `{ "accessToken": "..." }`.
Lỗi: `401` nếu cookie thiếu/sai/hết hạn.

#### `POST /api/v1/auth/logout` — 200
Xóa cookie `refreshToken`. Response `result`: `null`.

#### `GET /api/v1/auth/me` — 200
Cần Bearer. Response `result`: `User`.

### 4.2. User / Profile

#### `PUT /api/v1/user/profile` — 200
Cần Bearer. Request (tất cả tùy chọn, ít nhất 1 trường):
```json
{ "fullName": "Alice Nguyễn", "avatarUrl": "https://..." }
```
Response `result`: `User`.

#### `PUT /api/v1/user/password` — 200
Cần Bearer.
```json
{ "oldPassword": "Secret123", "newPassword": "NewSecret456" }
```
Lỗi: `400` nếu `oldPassword` sai. Response `result`: `null`.

### 4.3. Chat & AI Gateway

#### `GET /api/v1/chat/conversations` — 200
Cần Bearer. Query: `page` (default 1), `limit` (default 20, max 100).
Response: `Paginated<Conversation>` — sắp xếp `updatedAt` giảm dần.

#### `POST /api/v1/chat/conversations` — 201
Cần Bearer. Request:
```json
{ "title": "Tư vấn thừa kế" }
```
`title` tùy chọn, default `"Cuộc trò chuyện mới"`.
Response `result`: `Conversation`.

#### `DELETE /api/v1/chat/conversations/:id` — 200
Cần Bearer. Chỉ chủ sở hữu. Response `result`: `null`.
Lỗi: `404` nếu không tồn tại, `403` nếu không phải chủ.

#### `GET /api/v1/chat/conversations/:id/messages` — 200
Cần Bearer. Query: `page`, `limit`.
Response: `Paginated<Message>` — sắp xếp `createdAt` tăng dần.
Lỗi: `404` nếu conversation không tồn tại; `403` nếu không phải chủ.

#### `POST /api/v1/chat/conversations/:id/messages` — 201
Cần Bearer. Request:
```json
{ "content": "Điều 1 Hiến pháp 2013 quy định gì?" }
```
Luồng xử lý:
1. Lưu message `sender=user`.
2. Gọi Backend `POST http://localhost:8090/api/retrieval` body `{ "query_text": content }`.
3. Nhận `result` (RetrievalResult).
4. Sinh nội dung trả lời của bot từ `result` (tối thiểu: tổng hợp `related_nodes[].text`/`citation`; nếu rỗng thì thông báo không tìm thấy).
5. Lưu message `sender=bot`: `content` = câu trả lời, `extractedHierarchy` = `result.extracted_hierarchy`, `relatedNodes` = `result.related_nodes`, `metadata` = `{ "responseTimeMs": <int> }`.
6. Cập nhật `conversations.updated_at`.

Response `result`: `ChatReply`.
Lỗi: `502` nếu Backend không phản hồi hợp lệ (kèm message thân thiện).
> Nếu Backend `success=false` hoặc lỗi mạng → Services vẫn lưu message `sender=bot` với nội dung thông báo lỗi thân thiện và trả `502`.

### 4.4. Admin (role `admin`, ngược lại `403`)

#### `GET /api/v1/admin/users` — 200
Query: `page`, `limit`, `search` (tùy chọn, tìm theo email/username).
Response: `Paginated<User>`.

#### `PUT /api/v1/admin/users/:id/status` — 200
```json
{ "isActive": false }
```
Response `result`: `User`. Lỗi: `404` nếu không có user.

#### `GET /api/v1/admin/analytics` — 200
```json
{ "totalUsers": 120, "totalConversations": 340, "totalQuestions": 1500 }
```

### 4.5. Health

#### `GET /api/v1/health` — 200 (không cần auth)
```json
{ "success": true, "statusCode": 200, "message": "OK", "result": { "status": "ok", "timestamp": "2026-10-20T10:00:00Z" } }
```

---

## 5. DB Schema (PostgreSQL)

### `users`
| Cột | Kiểu | Ràng buộc |
| --- | ---- | --------- |
| id | uuid | PK, default gen_random_uuid() |
| email | varchar(255) | unique, not null |
| username | varchar(50) | unique, not null |
| password_hash | varchar(255) | not null |
| full_name | varchar(255) | null |
| avatar_url | text | null |
| role | varchar(20) | not null, default 'user' (user\|admin) |
| is_active | boolean | not null, default true |
| created_at | timestamptz | not null, default now() |
| updated_at | timestamptz | not null, default now() |

### `conversations`
| Cột | Kiểu | Ràng buộc |
| --- | ---- | --------- |
| id | uuid | PK |
| user_id | uuid | FK → users.id, not null, ON DELETE CASCADE |
| title | varchar(255) | not null, default 'Cuộc trò chuyện mới' |
| created_at | timestamptz | not null, default now() |
| updated_at | timestamptz | not null, default now() |

### `messages`
| Cột | Kiểu | Ràng buộc |
| --- | ---- | --------- |
| id | uuid | PK |
| conversation_id | uuid | FK → conversations.id, not null, ON DELETE CASCADE |
| sender | varchar(10) | not null (user\|bot) |
| content | text | not null |
| extracted_hierarchy | jsonb | null |
| related_nodes | jsonb | null |
| metadata | jsonb | null |
| created_at | timestamptz | not null, default now() |

> Migrate bằng GORM `AutoMigrate` khi khởi động (đã chốt).

---

## 6. Biến môi trường (Services)

| Biến | Ý nghĩa | Ví dụ |
| ---- | ------- | ----- |
| `APP_PORT` | Cổng Services | `8080` |
| `GIN_MODE` | `debug` \| `release` | `debug` |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` / `DB_SSLMODE` | PostgreSQL | `localhost` / `5432` / `legalai` / `legalai` / `legalai` / `disable` |
| `JWT_SECRET` | Khóa ký access token | (>= 32 ký tự) |
| `JWT_ACCESS_TTL_MINUTES` | Hạn access token | `15` |
| `JWT_REFRESH_TTL_HOURS` | Hạn refresh token | `168` |
| `CORS_ALLOWED_ORIGINS` | Origin FE, phân tách `,` | `http://localhost:3002` |
| `AI_BACKEND_URL` | Base URL Backend | `http://localhost:8090` |
| `AI_BACKEND_TIMEOUT_SECONDS` | Timeout gọi AI | `60` |
| `COOKIE_SECURE` | Cookie Secure flag | `false` (dev) |

---

## 7. Biến môi trường (Frontend)

| Biến | Ý nghĩa | Giá trị |
| ---- | ------- | ------- |
| `NEXT_PUBLIC_API_BASE_URL` | Base URL Services | `http://localhost:8080/api/v1` |
| `PORT` | Cổng FE | `3002` |
