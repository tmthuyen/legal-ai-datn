# Báo cáo triển khai Frontend Legal AI (Subagent 2)

## 1. File tạo/sửa (frontend/)

### Tạo mới
- `src/apis/legal.api.ts` — API layer gộp auth/user/chat/admin theo contract (`docs/contracts/API_CONTRACT.md` §4)
- `src/shared/types/legal.types.ts` — Kiểu dữ liệu Legal AI khớp contract §3 (LegalUser, AuthResult, Conversation, Message, ChatReply, AdminAnalytics + payloads)
- `src/shared/utils/legal.ts` — Helpers narrow an toàn cho `relatedNodes`/`extractedHierarchy`, nhãn tiếng Việt
- `src/hooks/tankstack/useConversations.ts` — Hooks danh sách/tạo/xóa hội thoại (`GET/POST/DELETE /chat/conversations`)
- `src/hooks/tankstack/useChat.ts` — Hooks lịch sử tin nhắn + gửi (`GET/POST /chat/conversations/:id/messages`) + `useChat()` aggregate
- `src/hooks/tankstack/useProfile.ts` — `useUpdateProfile`, `useUpdatePassword`
- `src/hooks/tankstack/useAdminAnalytics.ts` — `useAdminUsers`, `useUpdateUserStatus`, `useAdminAnalytics`
- `src/components/legal/legal-citation.tsx` — Thẻ/ danh sách trích dẫn Điều/Khoản/Điểm (Collapsible)
- `src/components/legal/legal-hierarchy-breadcrumb.tsx` — Breadcrumb phân cấp luật từ `extractedHierarchy`
- `src/components/legal/chat-message-bubble.tsx` — Bong bóng tin nhắn (bot/user) hiển thị phân cấp + citations + metadata responseTimeMs
- `src/app/(main)/chat/page.tsx` — Trang hỏi đáp (Suspense)
- `src/app/(main)/chat/chat-workbench.tsx` — Khung chat: chọn/tạo hội thoại, gửi câu hỏi, hiển thị kết quả
- `src/app/(main)/conversations/page.tsx` — Trang quản lý hội thoại
- `src/app/(main)/conversations/conversations-client.tsx` — Danh sách phân trang, tạo/xóa, xem lịch sử tin nhắn
- `src/app/(admin-layout)/admin/dashboard/page.tsx` — Trang tổng quan admin
- `src/app/(admin-layout)/admin/dashboard/dashboard-client.tsx` — Thẻ thống kê analytics (totalUsers/conversations/questions)

### Sửa
- `.env.example` — `NEXT_PUBLIC_API_BASE_URL=http://localhost:8080/api/v1`
- `src/app/layout.tsx` — Metadata/title/description sang "Legal AI — Trợ đáp pháp lý Việt Nam"
- `src/shared/config/app.config.ts` — `appName` → "Legal AI", cập nhật mô tả tiếng Việt pháp luật
- `src/stores/auth.store.ts` — Chuyển sang dùng `LegalUser` (role string), bootstrap dùng `legalAuthApi` (refresh+getMe), helper `isAdminUser`
- `src/shared/utils/roleUtil.ts` — Rewrite theo `LegalUser.role` (string), helper map/route admin→`/admin/dashboard`
- `src/app/auth/login/login-form.tsx` — Login dùng `username`/`password`, gọi `legalAuthApi.login` + `getMe`, lưu token vào store
- `src/app/auth/signup/signup-form.tsx` — Register theo contract (email/username/password/fullName?), nối `legalAuthApi.register`
- `src/app/auth/login/page.tsx`, `src/app/auth/signup/page.tsx` — Metadata cập nhật Legal AI
- `src/app/auth/google-success/page.tsx` — Fix type nhỏ (an toàn)
- `src/app/(main)/(home)/page.tsx` — Landing page hoàn toàn Legal AI (corpus 5 văn bản, tính năng, CTA)
- `src/components/sidebar/nav-data.ts` — Nav Legal AI (Trang chủ/Hỏi đáp/Hội thoại, admin dashboard/users)
- `src/components/sidebar/nav-main.tsx` — Đồng bộ sử dụng NAV_SECTIONS
- `src/components/layout/header-search.tsx` — Submit → `/chat?q=`
- `src/components/layout/quick-nav-dropdown.tsx` — Link Legal AI, badge/role theo `LegalUser.role`
- `src/components/layout/user-menu.tsx` — Menu user Legal AI, sửa null-safe avatar, hiển thị role string
- `src/components/layout/RoleLayout.tsx`, `src/components/auth/RequireRole.tsx` — Sử dụng `roleUtil` mới
- `src/components/sidebar/user-sidebar.tsx` — Branding "Legal AI", link `/`
- `src/components/sidebar/admin-sidebar.tsx` — Branding "Legal AI", link `/admin/dashboard`
- `src/components/layout/user-header.tsx` — Branding "Legal AI"
- `src/components/header/admin-header.tsx` — Branding "Legal AI", link `/admin/dashboard`
- `src/components/layout/site-footer.tsx` — Footer Legal AI, links `/chat`, mô tả pháp luật
- `src/app/(main)/profile/ProfileForm.tsx` — Rewrite tabs (profile/security), bỏ movie sessions
- `src/app/(main)/profile/UserProfileForm.tsx` — Chỉ field hợp lệ contract (fullName, avatarUrl), hiển thị username/email/role/isActive, dùng `useUpdateProfile`
- `src/app/(main)/profile/UpdatePasswordForm.tsx` — Dùng `useUpdatePassword` (oldPassword/newPassword), validate confirm client, logout sau thành công
- `src/app/(main)/profile/page.tsx` — Cập nhật props
- `src/app/(admin-layout)/admin/users/users-client.tsx` — Rewrite cho `LegalUser`: search (email/username), pagination, lock/unlock (`PUT /admin/users/:id/status`), không tạo/sửa/xóa (không có API contract)
- `src/hooks/tankstack/useComment.ts` — Minor null-safe fix (avatar/fullName) giữ nguyên logic phim (không xóa)

## 2. Lệnh verify + kết quả thật (chạy từ `frontend/`)

```bash
cd frontend
npm install  # ✅ (hoàn tất)
npm run type-check  # ✅ tsc --noEmit — KHÔNG lỗi
npm run lint  # ✅ eslint — 0 lỗi, 62 warnings (pre-existing, không liên quan thay đổi)
npm run build  # ✅ next build — compiled thành công, 22 routes prerendered
```

Kết quả đầy đủ (đầu/cuối):
- `type-check`: exit 0
- `lint`: "✖ 62 problems (0 errors, 62 warnings)" — exit 0
- `build`: "✓ Compiled successfully..." + routes: `/`, `/chat`, `/conversations`, `/admin/dashboard`, `/admin/users`, `/profile`, auth pages — thành công

## 3. Mapping phase → trạng thái

| Phase | Nội dung | Trạng thái | Ghi chú |
|---|---|---|---|
| 1 | Config & types | ✅ | `.env.example`, `legal.types.ts`, metadata/layout/config |
| 2 | API layer + hooks | ✅ | `legal.api.ts`, 4 hooks TanStack Query |
| 3 | Auth UI | ✅ | Login/Register theo username/password, kết nối Services, hiển thị lỗi envelope |
| 4 | Landing | ✅ | Legal AI landing (corpus 5 văn bản, features) |
| 5 | Chat | ✅ | `/chat` + components citation/breadcrumb/bubble, đọc `?q=`, narrow unknown an toàn |
| 6 | Conversations | ✅ | Danh sách phân trang, tạo/xóa, xem lịch sử messages |
| 7 | Profile | ✅ | Cập nhật profile/password theo contract, logout sau đổi mật khẩu |
| 8 | Admin | ✅ | Dashboard analytics + users (search+lock/unlock) theo contract |
| 9 | Verify | ✅ | Tất cả 4 lệnh pass |

## 4. Câu hỏi mở/chưa làm được + lý do

- **Google login**: Không có trong `docs/contracts/API_CONTRACT.md`. UI auth mới bỏ Google; `google-success/page.tsx` chỉ fix type nhỏ, không kích hoạt chức năng.
- **Admin create/edit/delete user, assign roles**: Contract §4.4 chỉ có `GET /admin/users`, `PUT /admin/users/:id/status`, `GET /admin/analytics`. Không có endpoint tạo/sửa/xóa/phân quyền → UI không triển khai (ẩn nút Thêm, bỏ dialog phân quyền động). Lý do: tuân thủ "KHÔNG bịa endpoint/field/kiểu ngoài contract".
- **Admin/roles route còn tồn tại** (`/admin/roles`) — là code phim cũ, được giữ nguyên theo yêu cầu "KHÔNG xóa code phim" (không render trong UI mới). Không ảnh hưởng build.
- **Movie-era hooks/components khác**: Giữ nguyên để không phá vỡ tính năng cũ (nếu có), đã sửa vài chỗ null-safe tối thiểu để type-check pass mà không thay đổi semantics.
- `relatedNodes`/`extractedHierarchy` là `unknown` trong contract: Đã implement `src/shared/utils/legal.ts` (narrow + filter) và render có điều kiện — an toàn, không giả định schema chặt.

## 5. Xác nhận

- ✅ **KHÔNG chạm `backend/` và `services/`** — Chỉ sửa/tạo trong `frontend/`.
- ✅ **KHÔNG xóa code phim** — Giữ toàn bộ code phim; chỉ không dùng để render UI mới, có sửa null-safe tối thiểu không ảnh hưởng logic.
- ✅ **KHÔNG commit git** — Thay đổi chỉ local, working tree dirty theo trạng thái repo.
- ✅ Tuân thủ contract tuyệt đối (username/password login, envelope `success/statusCode/message/result/pagination`, role string `user|admin`, không dùng localStorage cho accessToken, không `@ts-ignore`/`eslint-disable`/`any` cho dữ liệu API — dùng `unknown`+narrow).
- ✅ Verify toàn bộ pass: type-check/lint/build.
