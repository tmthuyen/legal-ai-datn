package user

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"server/internal/shared/apperror"
	"server/internal/shared/middleware"
	"server/internal/shared/response"
)

// Handler xử lý các HTTP request liên quan đến người dùng.
type Handler struct {
	svc *Service
}

// NewHandler tạo User Handler mới.
func NewHandler(svc *Service) *Handler {
	return &Handler{svc: svc}
}

// UpdateProfile xử lý PUT /api/v1/user/profile.
func (h *Handler) UpdateProfile(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, http.StatusUnauthorized, "Chưa xác thực người dùng", nil)
		return
	}

	var req UpdateProfileRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, http.StatusUnprocessableEntity, "Dữ liệu không hợp lệ", []string{err.Error()})
		return
	}

	user, err := h.svc.UpdateProfile(c.Request.Context(), userID, req)
	if err != nil {
		respondError(c, err)
		return
	}

	response.Success(c, http.StatusOK, "Cập nhật hồ sơ thành công", ToResponse(user))
}

// ChangePassword xử lý PUT /api/v1/user/password.
func (h *Handler) ChangePassword(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, http.StatusUnauthorized, "Chưa xác thực người dùng", nil)
		return
	}

	var req ChangePasswordRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, http.StatusUnprocessableEntity, "Dữ liệu không hợp lệ", []string{err.Error()})
		return
	}

	if err := h.svc.ChangePassword(c.Request.Context(), userID, req.OldPassword, req.NewPassword); err != nil {
		respondError(c, err)
		return
	}

	response.Success(c, http.StatusOK, "Đổi mật khẩu thành công", gin.H{"updated": true})
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
