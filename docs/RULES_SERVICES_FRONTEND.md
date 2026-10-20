# RULES — Services (Golang) & Frontend (Next.js)

> Trạng thái: **Chốt (v1)**
> Cập nhật: 2026-10-20
> Phạm vi: Rule cứng cho 2 scope `services/` (Golang) và `frontend/` (Next.js). Đọc kèm `docs/RULES.md` (rule chung toàn repo) và `docs/contracts/API_CONTRACT.md` (hợp đồng).
> **Subagent BẮT BUỘC tuân thủ.** Vi phạm = task chưa xong.

Mỗi mục là **một phạm vi riêng**, áp dụng độc lập.

| # | Phạm vi | Áp dụng cho |
| - | ------- | ----------- |
| 1 | Bất biến chung | Cả 2 scope |
| 2 | Kiến trúc & phân lớp | Cả 2 scope |
| 3 | Hợp đồng API (envelope) | `services/**`, `frontend/src/apis/**` |
| 4 | Cấm bịa đặt | Cả 2 scope |
| 5 | Cấu hình & bí mật | Cả 2 scope |
| 6 | Go coding rules | `services/**` |
| 7 | Next.js coding rules | `frontend/**` |
| 8 | Xác minh (verification) | Cả 2 scope |
| 9 | Git | Cả 2 scope |

---

## 1. Bất biến chung (không được vi phạm)

1. **KHÔNG sửa bất kỳ file nào trong `backend/`.** Backend FastAPI đóng băng trong V4.
2. **KHÔNG tạo endpoint/field/kiểu ngoài** `docs/contracts/API_CONTRACT.md`.
3. Frontend **KHÔNG** gọi trực tiếp Backend FastAPI; chỉ gọi Services.
4. **HTTP status header luôn bằng `statusCode` trong body.**
5. Không hardcode URL, cổng, credentials, secret, JWT key.
6. Mọi chức năng feature mới trong `frontend/` phải viết UI liên quan **pháp luật**; **không** dùng giao diện liên quan phim/giải trí để render.
7. **Chỉ commit khi được yêu cầu.** Không tự `git commit`/`push`.

## 2. Kiến trúc & phân lớp

**Phạm vi:** cả 2 scope.

- **Services**: logic nghiệp vụ nằm trong `internal/service`; handler mỏng, repository chỉ truy cập dữ liệu, không chứa business logic.
- **Frontend**: logic gọi API nằm trong `src/apis/**`; UI trong `src/app/**` + `src/components/**`; state toàn cục bằng Zustand trong `src/stores/**`; server-state bằng TanStack Query trong `src/hooks/tankstack/**`.
- Không nhân bản code đã có (envelope helper, axios client, auth store...). **Tái sử dụng** cái đang có.

## 3. Hợp đồng API (envelope)

**Phạm vi:** `services/**`, `frontend/src/apis/**`.

- Services **chỉ** trả response qua helper chuẩn:
  - `response.Success(c, statusCode, message, data)`
  - `response.Paginated(c, statusCode, message, data, pagination)`
  - `response.Error(c, statusCode, message, errors)`
  - **CẤM** tự `c.JSON(...)` rải rác trong handler.
- Payload dùng **camelCase** (`statusCode`, `accessToken`, `fullName`, `avatarUrl`, `isActive`, `createdAt`, `totalPages`).
- Frontend phải khai báo kiểu trong `src/shared/types/` khớp **chính xác** contract; **không** `any` cho dữ liệu API (dùng `unknown` + narrow nếu chưa chắc).
- Frontend đọc `result` từ `ApiResponse<T>`; lỗi đọc `ApiErrorResponse`.
- Lưu ý: `axiosClient` có interceptor `keysToCamel` → tên field snake_case từ server sẽ thành camelCase ở FE. Services vẫn phải trả camelCase (đúng contract) để không phụ thuộc interceptor.

## 4. Cấm bịa đặt (anti-hallucination)

**Phạm vi:** cả 2 scope.

- Cấm tạo endpoint không có trong `API_CONTRACT.md`.
- Cấm tạo field response không có trong contract (vd `refreshToken` **không** nằm trong `result` — nó ở cookie).
- Cấm tự đặt quy ước mới (tên field, mã lỗi, header) — nếu contract thiếu thì **dừng lại và hỏi**, ghi vào `docs/plans/` hoặc báo lại, không tự quyết.
- Cấm giả định endpoint Backend khác `POST /api/retrieval` và `GET /health`.

## 5. Cấu hình & bí mật

**Phạm vi:** cả 2 scope.

- Services đọc cấu hình từ `.env` (qua `internal/config`). Cung cấp `.env.example` đầy đủ; **không** commit `.env`.
- Frontend đọc `NEXT_PUBLIC_*` từ `.env.local`; cung cấp `.env.example`. **Không** commit `.env`.
- Cấm đặt secret thật (JWT key, DB password, API key) trong code hoặc file commit được.
- Cập nhật `.gitignore` cho `services/` (bỏ `.env`, `bin/`, `tmp/`) nếu cần.

## 6. Go coding rules

**Phạm vi:** `services/**`.

- **Module path:** `github.com/legalai/services` (hoặc tên trong `go.mod`).
- **Cấu trúc bắt buộc:**
  ```
  services/
    cmd/api/main.go
    internal/config/       # đọc .env, struct Config
    internal/domain/       # entity + interface repository
    internal/repository/   # GORM impl
    internal/service/      # business logic
    internal/handler/      # Gin handler (mỏng)
    internal/middleware/   # auth JWT, RBAC, error recovery, CORS, logger
    internal/aiclient/     # HTTP client gọi Backend FastAPI
    pkg/response/          # envelope helper
    pkg/jwt/               # ký/verify token
    pkg/hash/              # bcrypt
    migrations/            # (không bắt buộc vì auto-migrate)
  ```
- **Mọi exported func/type phải có doc comment** bắt đầu bằng tên (Go convention).
- **Xử lý lỗi tường minh**: không bỏ qua `err`; wrap bằng `fmt.Errorf("...: %w", err)`.
- **Không panic** trong handler; dùng middleware `Recovery` trả `500` envelope.
- Handler **không** tự format lỗi: trả lỗi qua helper `response.Error`; lỗi nghiệp vụ định nghĩa tập trung (vd `internal/domain/errors.go`) kèm `statusCode`.
- Format: `gofmt` + `goimports`. `go vet ./...` phải sạch.
- GORM: dùng `AutoMigrate` cho 3 model `User`, `Conversation`, `Message`.
- JWT: dùng `github.com/golang-jwt/jwt/v5`; access token HS256; phân quyền qua middleware `RequireAuth` và `RequireRole("admin")`.
- Password: `golang.org/x/crypto/bcrypt` (cost mặc định).
- Cookie refresh token: `HttpOnly`, `SameSite=Lax`, `Secure` theo `COOKIE_SECURE`, `Path=/`.
- **CORS**: chỉ cho origin từ `CORS_ALLOWED_ORIGINS`, `AllowCredentials=true`.

## 7. Next.js coding rules

**Phạm vi:** `frontend/**`.

- **Giữ** code phim cũ nhưng **không dùng để render** (theo quyết định của dev). Không xóa, không import vào UI mới.
- App Router (`src/app/**`). Component mặc định server component; chỉ thêm `'use client'` khi cần hook/state.
- UI dùng **shadcn/ui có sẵn** trong `src/components/ui/**` + Tailwind v4. **Cấm tự viết lại** component UI đã có (Button, Card, Input, Dialog, ...).
- **Không** dùng `localStorage` cho `accessToken` (giữ trong Zustand memory như hiện tại).
- Tái sử dụng `axiosClient` (`src/lib/axiosClient.ts`) — **không** tạo axios instance mới.
- Kiểu dữ liệu API khai báo trong `src/shared/types/` (thêm file mới `legal.types.ts` hoặc mở rộng `api.types.ts`), khớp contract.
- Gọi API: tạo `src/apis/legal.api.ts` (auth/chat/user/admin) + hook TanStack Query tương ứng.
- Trang phải có: Landing pháp luật, Login, Register, Chat hỏi đáp, Quản lý hội thoại, Profile, Admin.
- **Đổi metadata** trong `src/app/layout.tsx` sang Legal AI (title/description tiếng Việt). Cập nhật `src/shared/config/app.config.ts` (`name`, `description`).
- Comment/tên biến tiếng Việt, nhất quán với code hiện có.
- `npm run type-check`, `npm run lint`, `npm run build` phải pass.
- Cấm `@ts-ignore`, `eslint-disable`, `any` cho dữ liệu API.

## 8. Xác minh (verification)

**Phạm vi:** cả 2 scope. Subagent **tự chạy** trước khi báo xong:

- Services: `cd services && go mod tidy && go build ./... && go vet ./...`
- Frontend: `cd frontend && npm install && npm run type-check && npm run lint && npm run build`
- Không cần PostgreSQL/Neo4j chạy sẵn. Nếu build cần DB thì tách để build không phụ thuộc kết nối runtime.
- Báo cáo lại: file đã tạo/sửa, lệnh đã chạy, kết quả (pass/fail), phần chưa làm được + lý do.

## 9. Git

**Phạm vi:** cả 2 scope.

- **Không tự commit/push.** Chỉ khi dev yêu cầu.
- Không commit `.env`, `node_modules`, `bin/`, file build.
