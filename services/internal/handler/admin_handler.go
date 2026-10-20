package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"github.com/legalai/services/internal/service"
	"github.com/legalai/services/pkg/response"
)

// AdminHandler xử lý các endpoint quản trị (role admin).
type AdminHandler struct {
	admin *service.AdminService
}

// NewAdminHandler tạo AdminHandler mới.
func NewAdminHandler(admin *service.AdminService) *AdminHandler {
	return &AdminHandler{admin: admin}
}

// updateStatusRequest là body của PUT /admin/users/:id/status.
type updateStatusRequest struct {
	IsActive *bool `json:"isActive" binding:"required"`
}

// analyticsResponse là payload thống kê dashboard admin.
type analyticsResponse struct {
	TotalUsers         int64 `json:"totalUsers"`
	TotalConversations int64 `json:"totalConversations"`
	TotalQuestions     int64 `json:"totalQuestions"`
}

// ListUsers xử lý GET /api/v1/admin/users — 200 (phân trang, có `search`).
func (h *AdminHandler) ListUsers(c *gin.Context) {
	params := parsePagination(c)
	search := c.Query("search")

	users, pagination, err := h.admin.ListUsers(c.Request.Context(), params, search)
	if err != nil {
		respondBusinessError(c, err)
		return
	}

	response.Paginated(c, http.StatusOK, "Lấy danh sách thành công", toUserList(users), toPageMeta(pagination))
}

// UpdateUserStatus xử lý PUT /api/v1/admin/users/:id/status — 200.
func (h *AdminHandler) UpdateUserStatus(c *gin.Context) {
	userID, valid := parseUUID(c.Param("id"))
	if !valid {
		response.Error(c, 400, "ID người dùng không hợp lệ", nil)
		return
	}

	var request updateStatusRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		response.Error(c, 422, "Dữ liệu không hợp lệ", []string{err.Error()})
		return
	}

	user, err := h.admin.UpdateUserStatus(c.Request.Context(), userID, *request.IsActive)
	if err != nil {
		respondBusinessError(c, err)
		return
	}

	response.Success(c, http.StatusOK, "Cập nhật trạng thái thành công", toUserResponse(user))
}

// Analytics xử lý GET /api/v1/admin/analytics — 200.
func (h *AdminHandler) Analytics(c *gin.Context) {
	analytics, err := h.admin.GetAnalytics(c.Request.Context())
	if err != nil {
		respondBusinessError(c, err)
		return
	}

	response.Success(c, http.StatusOK, "Lấy thống kê thành công", analyticsResponse{
		TotalUsers:         analytics.TotalUsers,
		TotalConversations: analytics.TotalConversations,
		TotalQuestions:     analytics.TotalQuestions,
	})
}
