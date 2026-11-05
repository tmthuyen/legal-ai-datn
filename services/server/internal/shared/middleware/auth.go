// Package middleware cung cấp các HTTP middleware dùng chung trong hệ thống.
package middleware

import (
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"

	"server/internal/shared/jwt"
	"server/internal/shared/response"
)

const (
	// ContextUserIDKey là context key lưu UserID đã xác thực.
	ContextUserIDKey = "userID"
	// ContextUserRoleKey là context key lưu Role của user.
	ContextUserRoleKey = "userRole"
)

// RequireAuth xác thực access token từ Authorization header (Bearer format).
func RequireAuth(jwtManager *jwt.Manager) gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			response.Error(c, 401, "Yêu cầu đăng nhập", []string{"Thiếu header Authorization"})
			c.Abort()
			return
		}

		parts := strings.SplitN(authHeader, " ", 2)
		if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") {
			response.Error(c, 401, "Header Authorization không đúng định dạng Bearer", nil)
			c.Abort()
			return
		}

		claims, err := jwtManager.VerifyToken(parts[1], jwt.TypeAccess)
		if err != nil {
			response.Error(c, 401, "Token không hợp lệ hoặc đã hết hạn", []string{err.Error()})
			c.Abort()
			return
		}

		c.Set(ContextUserIDKey, claims.UserID)
		c.Set(ContextUserRoleKey, claims.Role)
		c.Next()
	}
}

// RequireRole kiểm tra quyền của người dùng hiện tại có khớp với role yêu cầu.
func RequireRole(expectedRole string) gin.HandlerFunc {
	return func(c *gin.Context) {
		roleVal, exists := c.Get(ContextUserRoleKey)
		if !exists {
			response.Error(c, 403, "Không đủ quyền truy cập", nil)
			c.Abort()
			return
		}

		role, ok := roleVal.(string)
		if !ok || role != expectedRole {
			response.Error(c, 403, "Yêu cầu quyền quản trị viên", nil)
			c.Abort()
			return
		}

		c.Next()
	}
}

// CurrentUserID trích xuất UserID từ Gin context.
func CurrentUserID(c *gin.Context) (uuid.UUID, bool) {
	val, exists := c.Get(ContextUserIDKey)
	if !exists {
		return uuid.Nil, false
	}
	id, ok := val.(uuid.UUID)
	return id, ok
}

// CurrentUserRole trích xuất Role từ Gin context.
func CurrentUserRole(c *gin.Context) (string, bool) {
	val, exists := c.Get(ContextUserRoleKey)
	if !exists {
		return "", false
	}
	role, ok := val.(string)
	return role, ok
}
