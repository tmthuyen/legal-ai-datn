package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"github.com/legalai/services/internal/middleware"
	"github.com/legalai/services/internal/service"
	"github.com/legalai/services/pkg/response"
)

// ChatHandler xử lý các endpoint hội thoại và gửi câu hỏi pháp lý.
type ChatHandler struct {
	chat *service.ChatService
}

// NewChatHandler tạo ChatHandler mới.
func NewChatHandler(chat *service.ChatService) *ChatHandler {
	return &ChatHandler{chat: chat}
}

// createConversationRequest là body của POST /chat/conversations.
type createConversationRequest struct {
	Title string `json:"title"`
}

// sendMessageRequest là body của POST /chat/conversations/:id/messages.
type sendMessageRequest struct {
	Content string `json:"content" binding:"required"`
}

// ListConversations xử lý GET /api/v1/chat/conversations — 200 (phân trang).
func (h *ChatHandler) ListConversations(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, 401, "Chưa xác thực người dùng", nil)
		return
	}

	params := parsePagination(c)
	conversations, pagination, err := h.chat.ListConversations(c.Request.Context(), userID, params)
	if err != nil {
		respondBusinessError(c, err)
		return
	}

	response.Paginated(c, http.StatusOK, "Lấy danh sách thành công", toConversationList(conversations), toPageMeta(pagination))
}

// CreateConversation xử lý POST /api/v1/chat/conversations — 201.
func (h *ChatHandler) CreateConversation(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, 401, "Chưa xác thực người dùng", nil)
		return
	}

	var request createConversationRequest
	// Body có thể rỗng (title tùy chọn) — chỉ báo lỗi khi JSON sai cú pháp.
	if c.Request.ContentLength > 0 {
		if err := c.ShouldBindJSON(&request); err != nil {
			response.Error(c, 422, "Dữ liệu không hợp lệ", []string{err.Error()})
			return
		}
	}

	conversation, err := h.chat.CreateConversation(c.Request.Context(), userID, request.Title)
	if err != nil {
		respondBusinessError(c, err)
		return
	}

	response.Success(c, http.StatusCreated, "Tạo hội thoại thành công", toConversationResponse(conversation))
}

// DeleteConversation xử lý DELETE /api/v1/chat/conversations/:id — 200.
func (h *ChatHandler) DeleteConversation(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, 401, "Chưa xác thực người dùng", nil)
		return
	}

	conversationID, valid := parseUUID(c.Param("id"))
	if !valid {
		response.Error(c, 400, "ID hội thoại không hợp lệ", nil)
		return
	}

	if err := h.chat.DeleteConversation(c.Request.Context(), userID, conversationID); err != nil {
		respondBusinessError(c, err)
		return
	}

	response.Success(c, http.StatusOK, "Xoá hội thoại thành công", nil)
}

// ListMessages xử lý GET /api/v1/chat/conversations/:id/messages — 200 (phân trang).
func (h *ChatHandler) ListMessages(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, 401, "Chưa xác thực người dùng", nil)
		return
	}

	conversationID, valid := parseUUID(c.Param("id"))
	if !valid {
		response.Error(c, 400, "ID hội thoại không hợp lệ", nil)
		return
	}

	params := parsePagination(c)
	messages, pagination, err := h.chat.ListMessages(c.Request.Context(), userID, conversationID, params)
	if err != nil {
		respondBusinessError(c, err)
		return
	}

	response.Paginated(c, http.StatusOK, "Lấy danh sách thành công", toMessageList(messages), toPageMeta(pagination))
}

// SendMessage xử lý POST /api/v1/chat/conversations/:id/messages — 201.
func (h *ChatHandler) SendMessage(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, 401, "Chưa xác thực người dùng", nil)
		return
	}

	conversationID, valid := parseUUID(c.Param("id"))
	if !valid {
		response.Error(c, 400, "ID hội thoại không hợp lệ", nil)
		return
	}

	var request sendMessageRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		response.Error(c, 422, "Dữ liệu không hợp lệ", []string{err.Error()})
		return
	}

	reply, err := h.chat.SendMessage(c.Request.Context(), userID, conversationID, request.Content)
	if err != nil {
		// Khi Backend AI lỗi, bot message thân thiện đã được lưu; trả lỗi 502 theo contract.
		respondBusinessError(c, err)
		return
	}

	response.Success(c, http.StatusCreated, "Gửi câu hỏi thành công", chatReplyResponse{
		UserMessage: toMessageResponse(reply.UserMessage),
		BotMessage:  toMessageResponse(reply.BotMessage),
	})
}
