# PLAN INDEX

> File thống kê/tổng hợp plans trong `docs/plans/`. Mục đích: giúp agent biết index hiện tại và next index, tránh trùng/sai số thứ tự.

## Quy tắc đặt tên plan

Theo `AGENTS.md` (repo hiện tại):  
- Đặt tên: `V{index}_{scope}_{task_name}.md`
- `{index}`: số thứ tự liên tục (0,1,2,...)
- `{scope}`: ∈ `backend` | `frontend` | `cicd` | `ai`
- `{task_name}`: slug `kebab-case`
- Tiêu đề: `# V{index} — <mô tả>`
- Lưu tại: `docs/plans/`
- Khi tạo plan mới: đọc file này → `next_index = max(index)+1`, đặt tên `V{next_index}_{scope}_{task_name}.md`, sau đó cập nhật index này.

> Chỉ rename file sau khi có xác nhận từ người dùng.

## Danh sách plan hiện có

| Index | Scope | Task name | Tên file | Trạng thái | Mô tả ngắn | File liên quan |
|---|---|---|---|---|---|---|
| 0 | init | init-plan | [V0_init-plan.md](./V0_init-plan.md) | — (rỗng) | Khởi tạo | — |
| 1 | backend | retrieval-target-validation | [V1_retrieval_target_validation.md](./V1_retrieval_target_validation.md) | Đang triển khai | Pipeline retrieval (parse/validate/resolve) | `scripts/test_retrieval.py`, `src/graph/*` |
| 2 | backend | retrieval-api | [V2_retrieval_api.md](./V2_retrieval_api.md) | Hoàn thành | FastAPI server cho Retrieval | `src/api/*` |
| 3 | cicd | ci-cd-split-workflows | [V3_cicd_ci-cd-split-workflows.md](./V3_cicd_ci-cd-split-workflows.md) | Hoàn thành | Chia CI/CD thành 6 workflow | `.github/workflows/*` |
| 4 | services | services-frontend-integration | [V4_services_frontend_integration.md](./V4_services_frontend_integration.md) | Hoàn thành (Golang `services/` done; FE ở V5) | Tích hợp Golang Services & NextJS Frontend | `services/*`, `frontend/*` |
| 5 | frontend | legal-ai-ui | [V5_frontend_legal-ai-ui.md](./V5_frontend_legal-ai-ui.md) | Hoàn thành | Giao diện Legal AI kết nối Services (auth/chat/profile/admin) | `frontend/*` |

> **Ghi chú naming cần xác nhận:** `V4_services_frontend_integration.md` dùng `scope = services` (ngoài tập `backend|frontend|cicd|ai` trong AGENTS.md) và `task_name` có dấu `_` thay vì kebab-case. Đề xuất đổi thành `V4_frontend_services-integration.md` hoặc tách scope rõ ràng — **chỉ rename sau khi user xác nhận**, sau đó cập nhật lại dòng này.

## Next index

- **Max index:** 5  
- **next_index:** 6

## Cách dùng bởi agent

1. Đọc `docs/plans/PLAN_INDEX.md` trước khi tạo plan mới.  
2. Tính `next_index = max(index)+1`, chọn `scope` hợp lý (`backend/frontend/cicd/ai`), đặt `task_name` kebab-case.  
3. Tạo `V{next_index}_{scope}_{task_name}.md`, tuân thủ cấu trúc AGENTS.md.  
4. Cập nhật bảng này.  
5. **Chỉ commit khi được yêu cầu**.  
6. Nếu phát hiện sai số thứ tự/trùng → đề xuất sắp xếp lại, **chỉ rename sau xác nhận user**.