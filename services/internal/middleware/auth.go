// Package middleware cung cấp các middleware Gin dùng chung cho Services.
package middleware

import (
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"

	"github.com/legalai/services/internal/domain"
	"github.com/legalai/services/pkg/jwt"
	"github.com/legalai/services/pkg/response"
)

const (
	// ContextUserID là key lưu user ID trong gin.Context.
	ContextUserID = "userID"
	// ContextUserRole là key lưu role trong gin.Context.
	ContextUserRole = "userRole"
)

// RequireAuth xác thực header `Authorization: Bearer <accessToken>`.
// Thiếu/sai/hết hạn token → 401 envelope.
func RequireAuth(jwtManager *jwt.Manager) gin.HandlerFunc {
	return func(c *gin.Context) {
		header := c.GetHeader("Authorization")
		if header == "" {
			response.Error(c, 401, "Thiếu access token", []string{"Authorization header là bắt buộc"})
			c.Abort()
			return
		}

		parts := strings.SplitN(header, " ", 2)
		if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") || strings.TrimSpace(parts[1]) == "" {
			response.Error(c, 401, "Access token không hợp lệ", []string{"Định dạng phải là Bearer <token>"})
			c.Abort()
			return
		}

		claims, err := jwtManager.ParseAccess(strings.TrimSpace(parts[1]))
		if err != nil {
			response.Error(c, 401, "Access token không hợp lệ hoặc đã hết hạn", []string{err.Error()})
			c.Abort()
			return
		}

		c.Set(ContextUserID, claims.UserID)
		c.Set(ContextUserRole, claims.Role)
		c.Next()
	}
}

// RequireRole chặn request nếu role trong token không nằm trong danh sách cho phép (403).
func RequireRole(roles ...domain.Role) gin.HandlerFunc {
	allowed := make(map[string]struct{}, len(roles))
	for _, role := range roles {
		allowed[string(role)] = struct{}{}
	}

	return func(c *gin.Context) {
		role, exists := c.Get(ContextUserRole)
		if !exists {
			response.Error(c, 401, "Thiếu access token", []string{"Chưa xác thực người dùng"})
			c.Abort()
			return
		}

		roleValue, ok := role.(string)
		if !ok {
			response.Error(c, 403, "Không đủ quyền truy cập", nil)
			c.Abort()
			return
		}
		if _, ok := allowed[roleValue]; !ok {
			response.Error(c, 403, "Không đủ quyền truy cập", nil)
			c.Abort()
			return
		}
		c.Next()
	}
}

// CurrentUserID lấy user ID đã được RequireAuth gán vào context.
func CurrentUserID(c *gin.Context) (uuid.UUID, bool) {
	value, exists := c.Get(ContextUserID)
	if !exists {
		return uuid.Nil, false
	}
	userID, ok := value.(uuid.UUID)
	if !ok {
		return uuid.Nil, false
	}
	return userID, true
}
