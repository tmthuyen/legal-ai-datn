package admin

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"

	"server/internal/modules/user"
	"server/internal/shared/apperror"
	"server/internal/shared/pagination"
	"server/internal/shared/response"
)

// Handler xử lý các HTTP request quản trị viên.
type Handler struct {
	svc *Service
}

// NewHandler tạo Admin Handler mới.
func NewHandler(svc *Service) *Handler {
	return &Handler{svc: svc}
}

// ListUsers xử lý GET /api/v1/admin/users.
func (h *Handler) ListUsers(c *gin.Context) {
	params := pagination.Parse(c)
	search := c.Query("search")

	users, total, err := h.svc.ListUsers(c.Request.Context(), params, search)
	if err != nil {
		respondError(c, err)
		return
	}

	tot, pg, lim, totalPages := pagination.Meta(total, params)
	pageInfo := response.Pagination{
		Total:      tot,
		Page:       pg,
		Limit:      lim,
		TotalPages: totalPages,
	}

	response.Paginated(c, http.StatusOK, "Lấy danh sách người dùng thành công", user.ToResponseList(users), pageInfo)
}

// UpdateUserStatus xử lý PUT /api/v1/admin/users/:id/status.
func (h *Handler) UpdateUserStatus(c *gin.Context) {
	targetID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		response.Error(c, http.StatusBadRequest, "ID người dùng không hợp lệ", []string{err.Error()})
		return
	}

	var req UpdateUserStatusRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, http.StatusUnprocessableEntity, "Dữ liệu không hợp lệ", []string{err.Error()})
		return
	}

	updatedUser, err := h.svc.UpdateUserStatus(c.Request.Context(), targetID, req.IsActive)
	if err != nil {
		respondError(c, err)
		return
	}

	response.Success(c, http.StatusOK, "Cập nhật trạng thái người dùng thành công", user.ToResponse(updatedUser))
}

// Analytics xử lý GET /api/v1/admin/analytics.
func (h *Handler) Analytics(c *gin.Context) {
	analytics, err := h.svc.GetAnalytics(c.Request.Context())
	if err != nil {
		response.Error(c, http.StatusInternalServerError, "Lấy dữ liệu thống kê thất bại", []string{err.Error()})
		return
	}

	response.Success(c, http.StatusOK, "Lấy thống kê thành công", analytics)
}

func respondError(c *gin.Context, err error) {
	if bErr, ok := apperror.AsBusinessError(err); ok {
		var details []string
		if bErr.Detail != "" {
			details = []string{bErr.Detail}
		}
		response.Error(c, bErr.StatusCode, bErr.Message, details)
		return
	}
	response.Error(c, http.StatusInternalServerError, "Lỗi máy chủ nội bộ", []string{err.Error()})
}
