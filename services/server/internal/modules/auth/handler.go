package auth

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"server/internal/modules/user"
	"server/internal/shared/apperror"
	"server/internal/shared/jwt"
	"server/internal/shared/middleware"
	"server/internal/shared/response"
)

const refreshTokenCookieName = "refresh_token"

// Handler xử lý các HTTP request xác thực người dùng.
type Handler struct {
	svc          *Service
	jwt          *jwt.Manager
	cookieSecure bool
}

// NewHandler tạo Auth Handler mới.
func NewHandler(svc *Service, jwtMgr *jwt.Manager, cookieSecure bool) *Handler {
	return &Handler{
		svc:          svc,
		jwt:          jwtMgr,
		cookieSecure: cookieSecure,
	}
}

// Register xử lý POST /api/v1/auth/register.
func (h *Handler) Register(c *gin.Context) {
	var req RegisterRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, http.StatusUnprocessableEntity, "Dữ liệu không hợp lệ", []string{err.Error()})
		return
	}

	pair, err := h.svc.Register(c.Request.Context(), req)
	if err != nil {
		respondError(c, err)
		return
	}

	h.setRefreshTokenCookie(c, pair.RefreshToken)
	res := Response{
		AccessToken: pair.AccessToken,
		User:        user.ToResponse(pair.User),
	}
	response.Success(c, http.StatusCreated, "Đăng ký thành công", res)
}

// Login xử lý POST /api/v1/auth/login.
func (h *Handler) Login(c *gin.Context) {
	var req LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, http.StatusUnprocessableEntity, "Dữ liệu không hợp lệ", []string{err.Error()})
		return
	}

	pair, err := h.svc.Login(c.Request.Context(), req)
	if err != nil {
		respondError(c, err)
		return
	}

	h.setRefreshTokenCookie(c, pair.RefreshToken)
	res := Response{
		AccessToken: pair.AccessToken,
		User:        user.ToResponse(pair.User),
	}
	response.Success(c, http.StatusOK, "Đăng nhập thành công", res)
}

// Refresh xử lý POST /api/v1/auth/refresh.
func (h *Handler) Refresh(c *gin.Context) {
	refreshToken, err := c.Cookie(refreshTokenCookieName)
	if err != nil || refreshToken == "" {
		response.Error(c, http.StatusUnauthorized, "Yêu cầu đăng nhập lại", []string{"Không tìm thấy refresh token trong cookie"})
		return
	}

	newAccessToken, err := h.svc.RefreshToken(c.Request.Context(), refreshToken)
	if err != nil {
		respondError(c, err)
		return
	}

	response.Success(c, http.StatusOK, "Làm mới token thành công", gin.H{"accessToken": newAccessToken})
}

// Logout xử lý POST /api/v1/auth/logout.
func (h *Handler) Logout(c *gin.Context) {
	h.clearRefreshTokenCookie(c)
	response.Success(c, http.StatusOK, "Đăng xuất thành công", gin.H{"loggedOut": true})
}

// Me xử lý GET /api/v1/auth/me.
func (h *Handler) Me(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, http.StatusUnauthorized, "Chưa xác thực người dùng", nil)
		return
	}

	currentUser, err := h.svc.GetCurrentUser(c.Request.Context(), userID)
	if err != nil {
		respondError(c, err)
		return
	}

	response.Success(c, http.StatusOK, "Lấy thông tin thành công", user.ToResponse(currentUser))
}

func (h *Handler) setRefreshTokenCookie(c *gin.Context, token string) {
	maxAge := h.jwt.RefreshTTLSeconds()
	c.SetSameSite(http.SameSiteLaxMode)
	c.SetCookie(refreshTokenCookieName, token, maxAge, "/", "", h.cookieSecure, true)
}

func (h *Handler) clearRefreshTokenCookie(c *gin.Context) {
	c.SetSameSite(http.SameSiteLaxMode)
	c.SetCookie(refreshTokenCookieName, "", -1, "/", "", h.cookieSecure, true)
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
