package admin

import (
	"github.com/gin-gonic/gin"
	"server/internal/shared/middleware"
)

// RegisterRoutes gắn các route của module Admin vào router group (bảo vệ bằng RequireRole admin).
func RegisterRoutes(rg *gin.RouterGroup, h *Handler, authMiddleware gin.HandlerFunc) {
	group := rg.Group("/admin", authMiddleware, middleware.RequireRole("admin"))
	group.GET("/users", h.ListUsers)
	group.PUT("/users/:id/status", h.UpdateUserStatus)
	group.GET("/analytics", h.Analytics)
}
