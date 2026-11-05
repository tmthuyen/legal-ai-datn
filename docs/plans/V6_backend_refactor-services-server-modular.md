# V6 — Refactor Kiến Trúc `services/server` Sang Modular Architecture (Package-by-Feature)

> **Trạng thái:** Hoàn thành (100% build & tests pass)  
> **Người thực hiện:** Developer & Antigravity  
> **Thời gian:** 2026-11-05  
> **Phạm vi (Scope):** `backend` (`services/server/**`)  
> **Next index theo `PLAN_INDEX.md`:** `6`  
> **Nguyên tắc thiết kế (Codebase Design):** Thiết kế các **Deep Modules** (nhiều hành vi nghiệp vụ ẩn sau interface gọn gàng, ranh giới seam rõ ràng), cấu trúc **Package-by-Feature**, chuẩn hoá **Entity DB - DTO - Repository - Service - Handler - Router**, tách bạch hạ tầng `infra/` và dùng chung `shared/`.

---

## 1. Bối cảnh & Mục Tiêu Kế Hoạch

### 1.1. Hiện trạng sau khi di chuyển thư mục
Mã nguồn đã được di chuyển an toàn từ `services/` sang `services/server/` bằng `git mv` (bảo toàn lịch sử commit). Tuy nhiên cấu trúc bên trong vẫn mang nhược điểm của mô hình cũ (*Package-by-Layer*):
- `internal/domain/entity.go` gộp chung `User`, `Conversation`, `Message`.
- `internal/handler/dto.go` gộp chung toàn bộ DTO request/response của cả hệ thống.
- Router tập trung tại một hàm lớn `buildRouter` trong `main.go`.
- Thiếu tầng hạ tầng chuẩn hoá (`infra/`) để tích hợp mở rộng Redis, Messaging, Observability.

### 1.2. Mục tiêu đạt được trong V6
1. **Tuân thủ triệt để quy tắc `AGENTS.md`, `RULES.md`, `RULES_SERVICES_FRONTEND.md` và `API_CONTRACT.md`**:
   - Giữ nguyên 100% hợp đồng API (16 endpoint, đường dẫn URL, cấu trúc envelope response `SuccessResponse[T]`, `ErrorResponse`, status code đồng nhất header & body).
   - Tuyệt đối không chạm vào `backend/` hay làm vỡ frontend `frontend/`.
2. **Áp dụng nguyên tắc Deep Modules (Codebase Design)**:
   - Mỗi module đóng gói toàn bộ logic của một ngữ cảnh nghiệp vụ (`auth`, `user`, `chat`, `admin`).
   - Interface repo/service nhỏ gọn, giấu kín sự phức tạp bên trong (seam rõ ràng, dễ test bằng unit test độc lập).
3. **Chuẩn hoá cấu trúc theo yêu cầu**:
   - `internal/modules/`: Chứa các tính năng theo domain. Mỗi module tự sở hữu: `entity.go` (DB), `dto.go` (Req/Res + mappers), `repository.go`, `service.go`, `handler.go`, `router.go`, `errors.go`.
   - `internal/infra/`: Quản lý các adapter hạ tầng bên ngoài (`config`, `database`, `redis`, `messaging`, `aiclient`, `httpserver`).
   - `internal/shared/`: Tiện ích dùng chung (`middleware`, `response`, `apperror`, `pagination`, `jwt`, `hash`).

---

## 2. Thiết Kế Chi Tiết Cấu Trúc Thư Mục `services/server/`

```text
services/server/
├── cmd/
│   └── api/
│       └── main.go                  # Bootstrap tối giản: init config, init infra, wire modules, start server
│
├── internal/
│   ├── modules/                     # CÁC BUSINESS MODULES (ĐÓNG GÓI RIÊNG BIỆT)
│   │   ├── auth/                    # Module Xác thực (Register, Login, Refresh, Me)
│   │   │   ├── dto.go               # RegisterRequest, LoginRequest, AuthResponse DTOs
│   │   │   ├── service.go           # Logic nghiệp vụ cấp token, hash password
│   │   │   ├── handler.go           # Gin HTTP Handler
│   │   │   └── router.go            # func RegisterRoutes(r *gin.RouterGroup, h *Handler, authMw gin.HandlerFunc)
│   │   │
│   │   ├── user/                    # Module Người dùng & Profile
│   │   │   ├── entity.go            # GORM Model User (Table: users)
│   │   │   ├── dto.go               # UpdateProfileRequest, ChangePasswordRequest, UserResponse DTOs
│   │   │   ├── repository.go        # Interface UserRepository + GORM implementation
│   │   │   ├── service.go           # Logic nghiệp vụ user
│   │   │   ├── handler.go           # HTTP Handler
│   │   │   └── router.go            # func RegisterRoutes(r *gin.RouterGroup, h *Handler, authMw gin.HandlerFunc)
│   │   │
│   │   ├── chat/                    # Module Hội thoại & AI Gateway
│   │   │   ├── entity.go            # GORM Model Conversation & Message (Tables: conversations, messages)
│   │   │   ├── dto.go               # SendMessageRequest, ConversationResponse, MessageResponse DTOs
│   │   │   ├── repository.go        # Interface + GORM repo cho Conversation & Message
│   │   │   ├── service.go           # Logic chat, gọi AIClient adapter, lưu lịch sử và citations
│   │   │   ├── handler.go           # HTTP Handler
│   │   │   └── router.go            # func RegisterRoutes(r *gin.RouterGroup, h *Handler, authMw gin.HandlerFunc)
│   │   │
│   │   └── admin/                   # Module Quản trị & Analytics
│   │       ├── dto.go               # AnalyticsResponse, UpdateStatusRequest DTOs
│   │       ├── service.go           # Thống kê analytics, cập nhật trạng thái user
│   │       ├── handler.go           # HTTP Handler
│   │       └── router.go            # func RegisterRoutes(r *gin.RouterGroup, h *Handler, adminMw gin.HandlerFunc)
│   │
│   ├── infra/                       # HẠ TẦNG KỸ THUẬT (INFRASTRUCTURE ADAPTERS)
│   │   ├── config/                  # Load biến môi trường .env sang Config struct
│   │   ├── database/                # GORM Postgres connection pool, AutoMigrate, Seeder
│   │   ├── redis/                   # Redis Client wrapper (Cache, Session, Lock - chuẩn bị mở rộng)
│   │   ├── messaging/               # Event Broker / Message Queue Interface (Producer/Consumer mẫu)
│   │   ├── aiclient/                # HTTP Client gọi Backend FastAPI AI (/api/retrieval)
│   │   └── httpserver/              # Wrapper chạy Gin server + Graceful shutdown an toàn
│   │
│   └── shared/                      # THÀNH PHẦN DÙNG CHUNG (CROSS-CUTTING CONCERNS)
│       ├── middleware/              # JWT Auth, RequireRole, CORS, Logger, Recovery
│       ├── response/                # Helper chuẩn: response.Success, response.Paginated, response.Error
│       ├── apperror/                # Business error definitions chuẩn hoá sang HTTP Status Code
│       ├── pagination/              # Cấu trúc PaginationParams & PageMeta
│       ├── jwt/                     # JWT Manager (HS256 access token + refresh token)
│       └── hash/                    # Bcrypt hashing helper
│
├── .env.example
├── go.mod
├── go.sum
└── README.md
```

---

## 3. Kiến Trúc Từng Module (Deep Module Design)

Mỗi module tuân thủ quy tắc **Interface là ranh giới (Seam)**:

### 3.1. Module `user`
* **`entity.go`**: Chứa duy nhất struct `User` ánh xạ tới bảng `users`, loại bỏ sự phụ thuộc ra ngoài domain.
* **`dto.go`**:
  - `UpdateProfileRequest`: Bind JSON `full_name`, `avatar_url`.
  - `ChangePasswordRequest`: Validate mật khẩu cũ, mật khẩu mới.
  - `UserResponse`: Trả về thông tin an toàn (loại bỏ trường nhạy cảm `password_hash`).
  - Hàm mapper: `ToUserResponse(u *User) UserResponse`.
* **`repository.go`**:
  - Interface `Repository`: `Create`, `FindByID`, `FindByUsername`, `FindByEmail`, `Update`, `List`, `Count`.
  - Struct `gormRepository`: Chứa `db *gorm.DB` cài đặt các hàm query (dùng `Preload`/`Joins` khi cần để triệt tiêu N+1).
* **`service.go`**: Nhận `Repository` interface qua constructor `NewService(repo Repository)`.
* **`handler.go`**: Xử lý request HTTP từ Gin context, gọi service, trả response qua `shared/response`.
* **`router.go`**:
  ```go
  func RegisterRoutes(rg *gin.RouterGroup, h *Handler, authMiddleware gin.HandlerFunc) {
      g := rg.Group("/user", authMiddleware)
      g.PUT("/profile", h.UpdateProfile)
      g.PUT("/password", h.ChangePassword)
  }
  ```

### 3.2. Module `chat`
* **`entity.go`**: Chứa struct `Conversation` và `Message` (kèm JSONB serializers cho metadata, citations).
* **`dto.go`**: `SendMessageRequest`, `CreateConversationRequest`, `ConversationResponse`, `MessageResponse`.
* **`repository.go`**: Interface `ConversationRepository` và `MessageRepository` + GORM implementation.
* **`service.go`**: Phụ thuộc `ConversationRepository`, `MessageRepository` và `aiclient.Client`. Điều phối lưu tin nhắn người dùng $\rightarrow$ gọi AI $\rightarrow$ lưu phản hồi AI.
* **`router.go`**: Đăng ký các endpoints `/chat/conversations` và `/chat/conversations/:id/messages`.

### 3.3. Module `auth`
* Tương tác với `user.Repository` và `shared/jwt` để đăng ký, đăng nhập, cấp refresh token vào cookie `HttpOnly`.

### 3.4. Module `admin`
* Phụ thuộc `user.Repository`, `chat.ConversationRepository`, `chat.MessageRepository` để thực hiện query analytics và cập nhật trạng thái user.
* Router được bảo vệ bởi middleware `shared/middleware.RequireRole(admin)`.

---

## 4. Kế Hoạch Triển Khai Từng Bước (Phased Execution)

### Phase 1: Xây dựng tầng `shared/` và `infra/`
1. Di chuyển các tiện ích từ `pkg/` sang `internal/shared/`:
   - `pkg/response` $\rightarrow$ `internal/shared/response`
   - `pkg/jwt` $\rightarrow$ `internal/shared/jwt`
   - `pkg/hash` $\rightarrow$ `internal/shared/hash`
2. Chuyển đổi lỗi nghiệp vụ:
   - `internal/domain/errors.go` $\rightarrow$ `internal/shared/apperror/errors.go`
   - `internal/domain/entity.go` (phần Pagination) $\rightarrow$ `internal/shared/pagination/pagination.go`
3. Chuyển đổi middleware:
   - `internal/middleware/*` $\rightarrow$ `internal/shared/middleware/*`
4. Xây dựng tầng `internal/infra/`:
   - `infra/config`: Kế thừa `internal/config/config.go`.
   - `infra/database`: Kế thừa `internal/repository/db.go` và `seed.go`.
   - `infra/aiclient`: Kế thừa `internal/aiclient/*`.
   - `infra/redis`: Tạo client Redis mẫu (hỗ trợ Cache Get/Set/Del với cơ chế No-Op nếu chưa cấu hình Redis).
   - `infra/messaging`: Tạo interface `EventBroker` mẫu (Publish / Subscribe).
   - `infra/httpserver`: Tạo hàm `Serve(srv *http.Server, port string) error` với Graceful Shutdown.

### Phase 2: Refactor các Modules (`internal/modules/`)
1. **Module `user`**:
   - Tạo `internal/modules/user/entity.go`
   - Tạo `internal/modules/user/dto.go`
   - Tạo `internal/modules/user/repository.go`
   - Tạo `internal/modules/user/service.go`
   - Tạo `internal/modules/user/handler.go`
   - Tạo `internal/modules/user/router.go`
2. **Module `chat`**:
   - Tạo `internal/modules/chat/entity.go`
   - Tạo `internal/modules/chat/dto.go`
   - Tạo `internal/modules/chat/repository.go`
   - Tạo `internal/modules/chat/service.go`
   - Tạo `internal/modules/chat/handler.go`
   - Tạo `internal/modules/chat/router.go`
3. **Module `auth`**:
   - Tạo `internal/modules/auth/dto.go`
   - Tạo `internal/modules/auth/service.go`
   - Tạo `internal/modules/auth/handler.go`
   - Tạo `internal/modules/auth/router.go`
4. **Module `admin`**:
   - Tạo `internal/modules/admin/dto.go`
   - Tạo `internal/modules/admin/service.go`
   - Tạo `internal/modules/admin/handler.go`
   - Tạo `internal/modules/admin/router.go`

### Phase 3: Wiring lại tại `cmd/api/main.go` & Dọn dẹp Code cũ
1. Cập nhật `cmd/api/main.go`:
   - Nạp `config` $\rightarrow$ Nạp `database` (AutoMigrate & Seed) $\rightarrow$ Khởi tạo `infra` & `modules` $\rightarrow$ Gọi `router.RegisterRoutes(...)` của từng module $\rightarrow$ Chạy server qua `httpserver.Serve`.
2. Xoá các thư mục cũ đã phân rã:
   - Xoá `internal/domain/`, `internal/repository/`, `internal/service/`, `internal/handler/`, `internal/aiclient/`, `internal/middleware/`, `pkg/`.
3. Cập nhật đường dẫn trong CI/CD workflow `.github/workflows/ci-services.yml` nếu cần: `working-directory: services/server`.

---

## 5. Kế Hoạch Xác Minh (Verification Plan)

### Automated Tests & Quality Gates
Tại thư mục `services/server`:
```powershell
# 1. Format code theo chuẩn Go
go fmt ./...

# 2. Kiểm tra lỗi cú pháp và package import
go vet ./...

# 3. Chạy unit tests hiện có
go test ./...

# 4. Biên dịch mã nguồn kiểm tra 100% build pass
go build -o bin/api.exe ./cmd/api
```

### Manual Verification
- Chạy thử `go run ./cmd/api/main.go`.
- Kiểm tra các endpoint qua file `req.http`:
  - `GET /api/v1/health` $\rightarrow$ Status 200 OK
  - `POST /api/v1/auth/login` $\rightarrow$ Đăng nhập thành công với tài khoản Admin mặc định
  - `GET /api/v1/chat/conversations` $\rightarrow$ Lấy danh sách hội thoại
  - `GET /api/v1/admin/analytics` $\rightarrow$ Trả về đúng số liệu thống kê

---

## 6. Cập Nhật Tài Liệu Tham Chiếu
- Cập nhật file `docs/plans/PLAN_INDEX.md` thêm dòng:
  `| 6 | backend | refactor-services-server-modular | V6_backend_refactor-services-server-modular.md | Đang triển khai | Refactor services/server sang cấu trúc modules/infra/shared | services/server/* |`
