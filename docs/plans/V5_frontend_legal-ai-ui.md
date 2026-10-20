# V5 — Frontend Legal AI: giao diện trợ đáp pháp lý kết nối Services Golang

> Trạng thái: **Hoàn thành** (verified: type-check + lint 0 errors + build pass)
> Người thực hiện: Subagent 2 (Frontend NextJS Engineer)
> Thời gian: 2026-10-20
> Phạm vi: Triển khai đầy đủ UI pháp luật trong `frontend/` (Next.js 16 + React 19 + TS + Tailwind v4 + shadcn/ui), kết nối tầng **Services Golang** theo `docs/contracts/API_CONTRACT.md`. **KHÔNG** sửa `backend/` và `services/`; **KHÔNG** xóa code phim (giữ nhưng không dùng để render).

## 1. Căn cứ

- `docs/contracts/API_CONTRACT.md` — nguồn sự thật duy nhất (endpoint/field/kiểu/envelope/env).
- `docs/RULES_SERVICES_FRONTEND.md` — §1 bất biến, §4 cấm bịa, §7 Next.js, §8 verify.
- `docs/architecture.md` — kiến trúc 3 khối, luồng E2E.
- `docs/plans/V4_services_frontend_integration.md` §5 Subagent 2.
- `frontend/AGENTS.md`.

## 2. Module liên quan

**Sửa:** `frontend/.env`, `frontend/.env.example`, `frontend/src/app/layout.tsx`,
`frontend/src/shared/config/app.config.ts`, `frontend/src/apis/auth.api.ts`,
`frontend/src/stores/auth.store.ts`, `frontend/src/components/layout/{user-sidebar,user-header,user-menu}.tsx`,
`frontend/src/components/sidebar/nav-data.ts`, `frontend/src/components/sidebar/nav-main.tsx`,
`frontend/src/components/loading/mobile-bottom-nav.tsx`, `frontend/src/shared/utils/roleUtil.ts`,
`frontend/src/app/auth/login/*`, `frontend/src/app/auth/signup/*`,
`frontend/src/app/(main)/(home)/page.tsx`, `frontend/src/app/(main)/profile/*`,
`frontend/src/app/(admin-layout)/admin/users/*`.

**Tạo mới:** `frontend/src/shared/types/legal.types.ts`, `frontend/src/apis/legal.api.ts`,
`frontend/src/hooks/tankstack/{useChat,useConversations,useAdminAnalytics,useProfile}.ts`,
`frontend/src/app/(main)/chat/**`, `frontend/src/components/legal/**`,
`frontend/src/app/(main)/conversations/**`, `frontend/src/app/(admin-layout)/admin/dashboard/**`.

## 3. Phases

| # | Phase | Nội dung | Trạng thái |
| - | ----- | -------- | ---------- |
| 1 | Config & types | `.env`/`.env.example` → `:8080/api/v1`; `legal.types.ts` khớp contract §3; metadata + `app.config.ts` sang Legal AI | ✅ |
| 2 | API layer | `legal.api.ts` (auth/user/chat/admin) bọc đúng endpoint contract; hook TanStack Query | ✅ |
| 3 | Auth UI | Login/Register kết nối Services; lưu `accessToken` vào store + `/auth/me`; hiển thị `message` lỗi | ✅ |
| 4 | Landing | Landing pháp luật (corpus 5 văn bản, tra cứu & hỏi đáp) | ✅ |
| 5 | Chat | `/chat` gửi câu hỏi; component trích dẫn Điều/Khoản/Điểm + breadcrumb + extractedHierarchy | ✅ |
| 6 | Conversations | Danh sách phân trang, tạo, xóa, xem lịch sử messages | ✅ |
| 7 | Profile | `PUT /user/profile` + `PUT /user/password` | ✅ |
| 8 | Admin | Danh sách user + search + khóa/mở (`PUT /admin/users/:id/status`) + analytics | ✅ |
| 9 | Verify | `npm install && npm run type-check && npm run lint && npm run build` | ✅ |

## 4. Bất biến áp dụng

- Không sửa `backend/`, `services/`; không xóa code phim.
- Không bịa endpoint/field/kiểu; không `localStorage` cho `accessToken`;
  không `@ts-ignore`/`eslint-disable`/`any` cho dữ liệu API.
- Tái sử dụng `axiosClient`, `useAuthStore`, shadcn/ui; không tạo axios instance mới.
- Không commit git.

## 5. Câu hỏi mở

- `relatedNodes`/`extractedHierarchy` là `unknown[]`/`Record<string,unknown>` trong contract → FE narrow an toàn khi render (đã implement `src/shared/utils/legal.ts`).
- Routes/movie code còn lại (`/admin/roles`, hooks API movie-era) được giữ nguyên theo yêu cầu "KHÔNG xóa code phim", chưa dùng trong UI mới. Không gây lỗi build (type-check/build pass).
- `google-success/page.tsx` có minimal type fix nhưng Google login không có trong contract; UI mới không hiển thị chức năng này.
