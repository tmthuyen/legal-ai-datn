package user

import "github.com/gin-gonic/gin"

// RegisterRoutes gắn các endpoint của module User vào router group.
func RegisterRoutes(rg *gin.RouterGroup, h *Handler, authMiddleware gin.HandlerFunc) {
	group := rg.Group("/user", authMiddleware)
	group.PUT("/profile", h.UpdateProfile)
	group.PUT("/password", h.ChangePassword)
}
