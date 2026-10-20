package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"github.com/legalai/services/internal/middleware"
	"github.com/legalai/services/internal/service"
	"github.com/legalai/services/pkg/jwt"
	"github.com/legalai/services/pkg/response"
)

// cookieRefreshToken là tên cookie chứa refresh token theo contract.
const cookieRefreshToken = "refreshToken"

// AuthHandler xử lý các endpoint xác thực.
type AuthHandler struct {
	auth         *service.AuthService
	jwtManager   *jwt.Manager
	cookieSecure bool
}

// NewAuthHandler tạo AuthHandler mới.
func NewAuthHandler(auth *service.AuthService, jwtManager *jwt.Manager, cookieSecure bool) *AuthHandler {
	return &AuthHandler{auth: auth, jwtManager: jwtManager, cookieSecure: cookieSecure}
}

// registerRequest là body của POST /auth/register.
type registerRequest struct {
	Email    string `json:"email" binding:"required"`
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
	FullName string `json:"fullName"`
}

// loginRequest là body của POST /auth/login.
type loginRequest struct {
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
}

// Register xử lý POST /api/v1/auth/register — 201.
func (h *AuthHandler) Register(c *gin.Context) {
	var request registerRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		response.Error(c, 422, "Dữ liệu không hợp lệ", []string{err.Error()})
		return
	}

	result, tokens, err := h.auth.Register(c.Request.Context(), service.RegisterInput{
		Email:    request.Email,
		Username: request.Username,
		Password: request.Password,
		FullName: request.FullName,
	})
	if err != nil {
		respondBusinessError(c, err)
		return
	}

	h.setRefreshCookie(c, tokens.RefreshToken)
	response.Success(c, http.StatusCreated, "Đăng ký thành công", authResultResponse{
		AccessToken: result.AccessToken,
		User:        toUserResponse(result.User),
	})
}

// Login xử lý POST /api/v1/auth/login — 200.
func (h *AuthHandler) Login(c *gin.Context) {
	var request loginRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		response.Error(c, 422, "Dữ liệu không hợp lệ", []string{err.Error()})
		return
	}

	result, tokens, err := h.auth.Login(c.Request.Context(), request.Username, request.Password)
	if err != nil {
		respondBusinessError(c, err)
		return
	}

	h.setRefreshCookie(c, tokens.RefreshToken)
	response.Success(c, http.StatusOK, "Đăng nhập thành công", authResultResponse{
		AccessToken: result.AccessToken,
		User:        toUserResponse(result.User),
	})
}

// Refresh xử lý POST /api/v1/auth/refresh — 200.
func (h *AuthHandler) Refresh(c *gin.Context) {
	refreshToken, err := c.Cookie(cookieRefreshToken)
	if err != nil {
		response.Error(c, 401, "Thiếu refresh token", nil)
		return
	}

	accessToken, businessErr := h.auth.Refresh(c.Request.Context(), refreshToken)
	if businessErr != nil {
		respondBusinessError(c, businessErr)
		return
	}

	response.Success(c, http.StatusOK, "Làm mới token thành công", gin.H{"accessToken": accessToken})
}

// Logout xử lý POST /api/v1/auth/logout — 200 (xoá cookie refresh token).
func (h *AuthHandler) Logout(c *gin.Context) {
	c.SetCookie(cookieRefreshToken, "", -1, "/", "", h.cookieSecure, true)
	response.Success(c, http.StatusOK, "Đăng xuất thành công", nil)
}

// Me xử lý GET /api/v1/auth/me — 200 (cần Bearer).
func (h *AuthHandler) Me(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, 401, "Chưa xác thực người dùng", nil)
		return
	}

	user, err := h.auth.Me(c.Request.Context(), userID)
	if err != nil {
		respondBusinessError(c, err)
		return
	}

	response.Success(c, http.StatusOK, "Lấy thông tin thành công", toUserResponse(user))
}

// setRefreshCookie ghi cookie refreshToken (HttpOnly, SameSite=Lax, Path=/).
func (h *AuthHandler) setRefreshCookie(c *gin.Context, token string) {
	maxAge := int(h.jwtManager.RefreshTTL().Seconds())
	c.SetSameSite(http.SameSiteLaxMode)
	c.SetCookie(cookieRefreshToken, token, maxAge, "/", "", h.cookieSecure, true)
}
