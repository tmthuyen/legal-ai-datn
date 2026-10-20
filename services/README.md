# Services — Legal AI (Golang + Gin + GORM + PostgreSQL)

Tầng Services đóng vai trò **Auth / User / RBAC / Quản lý hội thoại & AI Gateway** cho hệ thống Legal AI.
Services là nguồn sự thật duy nhất về người dùng, phiên đăng nhập và lịch sử hội thoại; trung chuyển
câu hỏi sang Backend FastAPI (`POST /api/retrieval`) và lưu kết quả trả về.

Nội dung gốc (mục tiêu ban đầu):

- Quản lý auth
- Quản lý user
- Quản lý chat_history
- Nhận các logs của model sau đổ đoán và lưu data vào database

> Hợp đồng API chính thức: `docs/contracts/API_CONTRACT.md`.
> Rule cứng: `docs/RULES_SERVICES_FRONTEND.md`.

---

## 1. Công nghệ

- Go 1.23+, **Gin** (`github.com/gin-gonic/gin`)
- **GORM** (`gorm.io/gorm`, `gorm.io/driver/postgres`) + `AutoMigrate` khi khởi động
- JWT `github.com/golang-jwt/jwt/v5` (HS256, access token) + refresh token trong cookie HttpOnly
- Bcrypt `golang.org/x/crypto/bcrypt`
- `github.com/google/uuid`, `github.com/joho/godotenv`

## 2. Cấu trúc thư mục

```
services/
  cmd/api/main.go            # entrypoint: wiring + AutoMigrate + Gin router
  internal/config/           # đọc .env → struct Config
  internal/domain/           # entity (User, Conversation, Message) + interface repository + errors.go
  internal/repository/       # GORM impl + db.go (kết nối, AutoMigrate)
  internal/service/          # auth_service, user_service, chat_service, admin_service
  internal/handler/          # auth/user/chat/admin/health handler (mỏng)
  internal/middleware/       # auth.go (RequireAuth, RequireRole), cors.go, recovery.go, logger.go
  internal/aiclient/         # HTTP client gọi Backend FastAPI POST /api/retrieval
  pkg/response/              # envelope: Success, Paginated, Error
  pkg/jwt/                   # ký/verify token
  pkg/hash/                  # bcrypt
```

## 3. Chạy Services

### 3.1. Chuẩn bị

1. Tạo file `.env` từ mẫu:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Điền giá trị thật, đặc biệt `JWT_SECRET` (>= 32 ký tự) và thông tin PostgreSQL.

### 3.2. Chạy

```powershell
cd services
go mod tidy
go run ./cmd/api
```

Services lắng nghe tại `http://localhost:8080`, prefix `/api/v1`. Kiểm tra nhanh:

```powershell
curl http://localhost:8080/api/v1/health
```

> Cần PostgreSQL đang chạy trước khi khởi động. `AutoMigrate` tự tạo 3 bảng `users`,
> `conversations`, `messages` khi Services khởi động. Backend FastAPI (`:8090`) cần chạy
> cho tính năng hỏi đáp; nếu không, endpoint gửi tin nhắn trả `502` (vẫn lưu bot message thân thiện).

## 4. Biến môi trường

Xem `.env.example` (khớp `docs/contracts/API_CONTRACT.md` §6): `APP_PORT`, `GIN_MODE`,
`DB_*`, `JWT_SECRET`, `JWT_ACCESS_TTL_MINUTES`, `JWT_REFRESH_TTL_HOURS`,
`CORS_ALLOWED_ORIGINS`, `AI_BACKEND_URL`, `AI_BACKEND_TIMEOUT_SECONDS`, `COOKIE_SECURE`.

## 5. Danh sách endpoint

Prefix `/api/v1`. Mọi response dùng envelope chuẩn; **HTTP status = `statusCode`**.

| Method | Path | Auth | Status |
| ------ | ---- | ---- | ------ |
| GET | `/health` | — | 200 |
| POST | `/auth/register` | — | 201 |
| POST | `/auth/login` | — | 200 |
| POST | `/auth/refresh` | cookie | 200 |
| POST | `/auth/logout` | — | 200 |
| GET | `/auth/me` | Bearer | 200 |
| PUT | `/user/profile` | Bearer | 200 |
| PUT | `/user/password` | Bearer | 200 |
| GET | `/chat/conversations` | Bearer | 200 |
| POST | `/chat/conversations` | Bearer | 201 |
| DELETE | `/chat/conversations/:id` | Bearer | 200 |
| GET | `/chat/conversations/:id/messages` | Bearer | 200 |
| POST | `/chat/conversations/:id/messages` | Bearer | 201 |
| GET | `/admin/users` | Bearer + admin | 200 |
| PUT | `/admin/users/:id/status` | Bearer + admin | 200 |
| GET | `/admin/analytics` | Bearer + admin | 200 |

## 6. Xác minh (verification)

```powershell
cd services
go mod tidy
go build ./...
go vet ./...
```

Ba lệnh phải pass. `go build` **không cần PostgreSQL đang chạy**: việc kết nối DB chỉ
xảy ra lúc runtime trong `cmd/api/main.go`, không có `init()` kết nối DB.
