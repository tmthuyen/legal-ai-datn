package chat

import "github.com/gin-gonic/gin"

// RegisterRoutes gắn các route của module Chat vào router group.
func RegisterRoutes(rg *gin.RouterGroup, h *Handler, authMiddleware gin.HandlerFunc) {
	group := rg.Group("/chat", authMiddleware)
	group.GET("/conversations", h.ListConversations)
	group.POST("/conversations", h.CreateConversation)
	group.DELETE("/conversations/:id", h.DeleteConversation)
	group.GET("/conversations/:id/messages", h.ListMessages)
	group.POST("/conversations/:id/messages", h.SendMessage)
}
