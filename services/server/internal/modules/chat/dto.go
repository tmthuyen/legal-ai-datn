package chat

import "time"

// CreateConversationRequest là payload của POST /api/v1/chat/conversations.
type CreateConversationRequest struct {
	Title string `json:"title"`
}

// SendMessageRequest là payload của POST /api/v1/chat/conversations/:id/messages.
type SendMessageRequest struct {
	Content string `json:"content" binding:"required"`
}

// ConversationResponse là DTO trả về cho hội thoại.
type ConversationResponse struct {
	ID        string `json:"id"`
	UserID    string `json:"userId"`
	Title     string `json:"title"`
	CreatedAt string `json:"createdAt"`
	UpdatedAt string `json:"updatedAt"`
}

// ToConversationResponse chuyển Conversation entity sang DTO.
func ToConversationResponse(c *Conversation) ConversationResponse {
	if c == nil {
		return ConversationResponse{}
	}
	return ConversationResponse{
		ID:        c.ID.String(),
		UserID:    c.UserID.String(),
		Title:     c.Title,
		CreatedAt: c.CreatedAt.Format(time.RFC3339),
		UpdatedAt: c.UpdatedAt.Format(time.RFC3339),
	}
}

// ToConversationList chuyển slice Conversation sang slice DTO.
func ToConversationList(items []Conversation) []ConversationResponse {
	res := make([]ConversationResponse, len(items))
	for i := range items {
		res[i] = ToConversationResponse(&items[i])
	}
	return res
}

// MessageResponse là DTO trả về cho tin nhắn.
type MessageResponse struct {
	ID                 string         `json:"id"`
	ConversationID     string         `json:"conversationId"`
	Sender             string         `json:"sender"`
	Content            string         `json:"content"`
	ExtractedHierarchy map[string]any `json:"extractedHierarchy,omitempty"`
	RelatedNodes       []any          `json:"relatedNodes,omitempty"`
	Metadata           map[string]any `json:"metadata,omitempty"`
	CreatedAt          string         `json:"createdAt"`
}

// ToMessageResponse chuyển Message entity sang DTO.
func ToMessageResponse(m *Message) MessageResponse {
	if m == nil {
		return MessageResponse{}
	}
	return MessageResponse{
		ID:                 m.ID.String(),
		ConversationID:     m.ConversationID.String(),
		Sender:             string(m.Sender),
		Content:            m.Content,
		ExtractedHierarchy: m.ExtractedHierarchy,
		RelatedNodes:       m.RelatedNodes,
		Metadata:           m.Metadata,
		CreatedAt:          m.CreatedAt.Format(time.RFC3339),
	}
}

// ToMessageList chuyển slice Message sang slice DTO.
func ToMessageList(items []Message) []MessageResponse {
	res := make([]MessageResponse, len(items))
	for i := range items {
		res[i] = ToMessageResponse(&items[i])
	}
	return res
}

// SendMessageResult là payload trả về gồm cả tin nhắn user và bot.
type SendMessageResult struct {
	UserMessage MessageResponse `json:"userMessage"`
	BotMessage  MessageResponse `json:"botMessage"`
}
