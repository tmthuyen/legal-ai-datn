package handler

import (
	"time"

	"github.com/google/uuid"

	"github.com/legalai/services/internal/domain"
)

// userResponse là payload User trả cho Frontend (camelCase, không có passwordHash).
type userResponse struct {
	ID        string  `json:"id"`
	Email     string  `json:"email"`
	Username  string  `json:"username"`
	FullName  *string `json:"fullName"`
	AvatarURL *string `json:"avatarUrl"`
	Role      string  `json:"role"`
	IsActive  bool    `json:"isActive"`
	CreatedAt string  `json:"createdAt"`
	UpdatedAt string  `json:"updatedAt"`
}

// toUserResponse chuyển entity User sang payload response.
func toUserResponse(user *domain.User) userResponse {
	return userResponse{
		ID:        user.ID.String(),
		Email:     user.Email,
		Username:  user.Username,
		FullName:  user.FullName,
		AvatarURL: user.AvatarURL,
		Role:      string(user.Role),
		IsActive:  user.IsActive,
		CreatedAt: formatTime(user.CreatedAt),
		UpdatedAt: formatTime(user.UpdatedAt),
	}
}

// toUserList chuyển danh sách entity User sang payload response.
func toUserList(users []domain.User) []userResponse {
	result := make([]userResponse, 0, len(users))
	for index := range users {
		result = append(result, toUserResponse(&users[index]))
	}
	return result
}

// authResultResponse là payload AuthResult (accessToken + user).
type authResultResponse struct {
	AccessToken string       `json:"accessToken"`
	User        userResponse `json:"user"`
}

// conversationResponse là payload Conversation trả cho Frontend.
type conversationResponse struct {
	ID        string `json:"id"`
	UserID    string `json:"userId"`
	Title     string `json:"title"`
	CreatedAt string `json:"createdAt"`
	UpdatedAt string `json:"updatedAt"`
}

// toConversationResponse chuyển entity Conversation sang payload response.
func toConversationResponse(conversation *domain.Conversation) conversationResponse {
	return conversationResponse{
		ID:        conversation.ID.String(),
		UserID:    conversation.UserID.String(),
		Title:     conversation.Title,
		CreatedAt: formatTime(conversation.CreatedAt),
		UpdatedAt: formatTime(conversation.UpdatedAt),
	}
}

// toConversationList chuyển danh sách entity Conversation sang payload response.
func toConversationList(conversations []domain.Conversation) []conversationResponse {
	result := make([]conversationResponse, 0, len(conversations))
	for index := range conversations {
		result = append(result, toConversationResponse(&conversations[index]))
	}
	return result
}

// messageResponse là payload Message trả cho Frontend.
type messageResponse struct {
	ID                 string         `json:"id"`
	ConversationID     string         `json:"conversationId"`
	Sender             string         `json:"sender"`
	Content            string         `json:"content"`
	ExtractedHierarchy map[string]any `json:"extractedHierarchy"`
	RelatedNodes       []any          `json:"relatedNodes"`
	Metadata           map[string]any `json:"metadata"`
	CreatedAt          string         `json:"createdAt"`
}

// toMessageResponse chuyển entity Message sang payload response.
func toMessageResponse(message *domain.Message) messageResponse {
	return messageResponse{
		ID:                 message.ID.String(),
		ConversationID:     message.ConversationID.String(),
		Sender:             string(message.Sender),
		Content:            message.Content,
		ExtractedHierarchy: toNullableMap(message.ExtractedHierarchy),
		RelatedNodes:       toNullableSlice(message.RelatedNodes),
		Metadata:           toNullableMap(message.Metadata),
		CreatedAt:          formatTime(message.CreatedAt),
	}
}

// toMessageList chuyển danh sách entity Message sang payload response.
func toMessageList(messages []domain.Message) []messageResponse {
	result := make([]messageResponse, 0, len(messages))
	for index := range messages {
		result = append(result, toMessageResponse(&messages[index]))
	}
	return result
}

// chatReplyResponse là payload ChatReply (userMessage + botMessage).
type chatReplyResponse struct {
	UserMessage messageResponse `json:"userMessage"`
	BotMessage  messageResponse `json:"botMessage"`
}

// toNullableMap trả nil khi map rỗng để JSON là null đúng contract.
func toNullableMap(value domain.JSONMap) map[string]any {
	if len(value) == 0 {
		return nil
	}
	return map[string]any(value)
}

// toNullableSlice trả nil khi slice rỗng để JSON là null đúng contract.
func toNullableSlice(value []any) []any {
	if len(value) == 0 {
		return nil
	}
	return value
}

// formatTime định dạng thời gian ISO-8601 UTC.
func formatTime(value time.Time) string {
	return value.UTC().Format(time.RFC3339)
}

// parseUUID phân tích chuỗi thành UUID; trả false nếu không hợp lệ.
func parseUUID(raw string) (uuid.UUID, bool) {
	parsed, err := uuid.Parse(raw)
	if err != nil {
		return uuid.Nil, false
	}
	return parsed, true
}
