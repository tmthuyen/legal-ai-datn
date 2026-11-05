package chat

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"

	"server/internal/shared/apperror"
	"server/internal/shared/middleware"
	"server/internal/shared/pagination"
	"server/internal/shared/response"
)

// Handler tiếp nhận các request liên quan đến hội thoại và gửi tin nhắn.
type Handler struct {
	svc *Service
}

// NewHandler tạo Handler mới.
func NewHandler(svc *Service) *Handler {
	return &Handler{svc: svc}
}

// ListConversations xử lý GET /api/v1/chat/conversations.
func (h *Handler) ListConversations(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, http.StatusUnauthorized, "Chưa xác thực người dùng", nil)
		return
	}

	params := pagination.Parse(c)
	conversations, total, err := h.svc.ListConversations(c.Request.Context(), userID, params)
	if err != nil {
		respondError(c, err)
		return
	}

	tot, pg, lim, totalPages := pagination.Meta(total, params)
	pageInfo := response.Pagination{
		Total:      tot,
		Page:       pg,
		Limit:      lim,
		TotalPages: totalPages,
	}

	response.Paginated(c, http.StatusOK, "Lấy danh sách thành công", ToConversationList(conversations), pageInfo)
}

// CreateConversation xử lý POST /api/v1/chat/conversations.
func (h *Handler) CreateConversation(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, http.StatusUnauthorized, "Chưa xác thực người dùng", nil)
		return
	}

	var req CreateConversationRequest
	if c.Request.ContentLength > 0 {
		if err := c.ShouldBindJSON(&req); err != nil {
			response.Error(c, http.StatusUnprocessableEntity, "Dữ liệu không hợp lệ", []string{err.Error()})
			return
		}
	}

	conv, err := h.svc.CreateConversation(c.Request.Context(), userID, req.Title)
	if err != nil {
		respondError(c, err)
		return
	}

	response.Success(c, http.StatusCreated, "Tạo hội thoại thành công", ToConversationResponse(conv))
}

// DeleteConversation xử lý DELETE /api/v1/chat/conversations/:id.
func (h *Handler) DeleteConversation(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, http.StatusUnauthorized, "Chưa xác thực người dùng", nil)
		return
	}

	convID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		response.Error(c, http.StatusBadRequest, "ID hội thoại không hợp lệ", []string{err.Error()})
		return
	}

	if err := h.svc.DeleteConversation(c.Request.Context(), userID, convID); err != nil {
		respondError(c, err)
		return
	}

	response.Success(c, http.StatusOK, "Xoá hội thoại thành công", gin.H{"deleted": true})
}

// ListMessages xử lý GET /api/v1/chat/conversations/:id/messages.
func (h *Handler) ListMessages(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, http.StatusUnauthorized, "Chưa xác thực người dùng", nil)
		return
	}

	convID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		response.Error(c, http.StatusBadRequest, "ID hội thoại không hợp lệ", []string{err.Error()})
		return
	}

	params := pagination.Parse(c)
	messages, total, err := h.svc.ListMessages(c.Request.Context(), userID, convID, params)
	if err != nil {
		respondError(c, err)
		return
	}

	tot, pg, lim, totalPages := pagination.Meta(total, params)
	pageInfo := response.Pagination{
		Total:      tot,
		Page:       pg,
		Limit:      lim,
		TotalPages: totalPages,
	}

	response.Paginated(c, http.StatusOK, "Lấy danh sách tin nhắn thành công", ToMessageList(messages), pageInfo)
}

// SendMessage xử lý POST /api/v1/chat/conversations/:id/messages.
func (h *Handler) SendMessage(c *gin.Context) {
	userID, ok := middleware.CurrentUserID(c)
	if !ok {
		response.Error(c, http.StatusUnauthorized, "Chưa xác thực người dùng", nil)
		return
	}

	convID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		response.Error(c, http.StatusBadRequest, "ID hội thoại không hợp lệ", []string{err.Error()})
		return
	}

	var req SendMessageRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, http.StatusUnprocessableEntity, "Nội dung câu hỏi không hợp lệ", []string{err.Error()})
		return
	}

	userMsg, botMsg, err := h.svc.SendMessage(c.Request.Context(), userID, convID, req.Content)
	if err != nil {
		respondError(c, err)
		return
	}

	result := SendMessageResult{
		UserMessage: ToMessageResponse(userMsg),
		BotMessage:  ToMessageResponse(botMsg),
	}

	response.Success(c, http.StatusOK, "Gửi tin nhắn thành công", result)
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
