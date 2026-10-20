package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"github.com/legalai/services/internal/middleware"
	"github.com/legalai/services/internal/service"
	"github.com/legalai/services/pkg/response"
)

// UserHandler xử lý các endpoint hồ sơ cá nhân.
type UserHandler struct {
	users *service.UserService
}

// NewUserHandler tạo UserHandler mới.
func NewUserHandler(users *service.UserService) *UserHandler {
	return &UserHandler{users: users}
}

// updateProfileRequest là body của PUT /user/profile (mọi trường tùy chọn).
type updateProfileRequest struct {
	FullName  *string `json:"fullName"`
	AvatarURL *string `json:"avatarUrl"`
}

// changePasswordRequest là body của PUT /user/password.
type changePasswordRequest struct {
	OldPassword string `json:"oldPassword" binding:"required"`
	NewPassword string `json:"newPassword" binding:"required"`
}

// UpdateProfile xử lý PUT /api/v1/user/profile — 200.
func (h *UserHandler) UpdateProfile(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, 401, "Chưa xác thực người dùng", nil)
		return
	}

	var request updateProfileRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		response.Error(c, 422, "Dữ liệu không hợp lệ", []string{err.Error()})
		return
	}

	user, err := h.users.UpdateProfile(c.Request.Context(), userID, service.UpdateProfileInput{
		FullName:  request.FullName,
		AvatarURL: request.AvatarURL,
	})
	if err != nil {
		respondBusinessError(c, err)
		return
	}

	response.Success(c, http.StatusOK, "Cập nhật hồ sơ thành công", toUserResponse(user))
}

// ChangePassword xử lý PUT /api/v1/user/password — 200.
func (h *UserHandler) ChangePassword(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, 401, "Chưa xác thực người dùng", nil)
		return
	}

	var request changePasswordRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		response.Error(c, 422, "Dữ liệu không hợp lệ", []string{err.Error()})
		return
	}

	if err := h.users.ChangePassword(c.Request.Context(), userID, request.OldPassword, request.NewPassword); err != nil {
		respondBusinessError(c, err)
		return
	}

	response.Success(c, http.StatusOK, "Đổi mật khẩu thành công", nil)
}
