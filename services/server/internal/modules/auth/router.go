package auth

import "github.com/gin-gonic/gin"

// RegisterRoutes gắn các route xác thực vào router group.
func RegisterRoutes(rg *gin.RouterGroup, h *Handler, authMiddleware gin.HandlerFunc) {
	group := rg.Group("/auth")
	group.POST("/register", h.Register)
	group.POST("/login", h.Login)
	group.POST("/refresh", h.Refresh)
	group.POST("/logout", h.Logout)
	group.GET("/me", authMiddleware, h.Me)
}
