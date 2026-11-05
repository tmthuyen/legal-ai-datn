package chat

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"

	"server/internal/infra/aiclient"
	"server/internal/shared/apperror"
	"server/internal/shared/pagination"
)

// Service điều phối nghiệp vụ hội thoại, tin nhắn và gọi Backend AI.
type Service struct {
	conversations ConversationRepository
	messages      MessageRepository
	ai            *aiclient.Client
}

// NewService tạo Service mới.
func NewService(
	conversations ConversationRepository,
	messages MessageRepository,
	ai *aiclient.Client,
) *Service {
	return &Service{
		conversations: conversations,
		messages:      messages,
		ai:            ai,
	}
}

const defaultConversationTitle = "Cuộc trò chuyện mới"

// ListConversations trả danh sách hội thoại của người dùng có phân trang.
func (s *Service) ListConversations(ctx context.Context, userID uuid.UUID, params pagination.Params) ([]Conversation, int64, error) {
	conversations, total, err := s.conversations.ListByUser(ctx, userID, params)
	if err != nil {
		return nil, 0, apperror.ErrInternal("Không thể lấy danh sách hội thoại", err.Error())
	}
	return conversations, total, nil
}

// CreateConversation tạo mới hội thoại.
func (s *Service) CreateConversation(ctx context.Context, userID uuid.UUID, title string) (*Conversation, error) {
	title = strings.TrimSpace(title)
	if title == "" {
		title = defaultConversationTitle
	}
	if len([]rune(title)) > 255 {
		return nil, apperror.ErrBadRequest("Tiêu đề hội thoại tối đa 255 ký tự")
	}

	conv := &Conversation{
		UserID: userID,
		Title:  title,
	}
	if err := s.conversations.Create(ctx, conv); err != nil {
		return nil, apperror.ErrInternal("Không thể tạo hội thoại", err.Error())
	}
	return conv, nil
}

// DeleteConversation xoá hội thoại (kiểm tra quyền sở hữu).
func (s *Service) DeleteConversation(ctx context.Context, userID, conversationID uuid.UUID) error {
	conv, err := s.conversations.FindByID(ctx, conversationID)
	if err != nil {
		return apperror.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	if conv == nil {
		return apperror.ErrNotFound("Không tìm thấy hội thoại")
	}
	if conv.UserID != userID {
		return apperror.ErrForbidden("Bạn không có quyền xoá hội thoại này")
	}

	if err := s.conversations.Delete(ctx, conversationID); err != nil {
		return apperror.ErrInternal("Không thể xoá hội thoại", err.Error())
	}
	return nil
}

// ListMessages lấy danh sách tin nhắn của hội thoại.
func (s *Service) ListMessages(ctx context.Context, userID, conversationID uuid.UUID, params pagination.Params) ([]Message, int64, error) {
	conv, err := s.conversations.FindByID(ctx, conversationID)
	if err != nil {
		return nil, 0, apperror.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	if conv == nil {
		return nil, 0, apperror.ErrNotFound("Không tìm thấy hội thoại")
	}
	if conv.UserID != userID {
		return nil, 0, apperror.ErrForbidden("Bạn không có quyền truy cập hội thoại này")
	}

	messages, total, err := s.messages.ListByConversation(ctx, conversationID, params)
	if err != nil {
		return nil, 0, apperror.ErrInternal("Không thể lấy danh sách tin nhắn", err.Error())
	}
	return messages, total, nil
}

// SendMessage lưu tin nhắn của user, gọi Backend AI, lưu câu trả lời bot và cập nhật hội thoại.
func (s *Service) SendMessage(ctx context.Context, userID, conversationID uuid.UUID, content string) (*Message, *Message, error) {
	content = strings.TrimSpace(content)
	if content == "" {
		return nil, nil, apperror.ErrBadRequest("Nội dung câu hỏi là bắt buộc")
	}

	conv, err := s.conversations.FindByID(ctx, conversationID)
	if err != nil {
		return nil, nil, apperror.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	if conv == nil {
		return nil, nil, apperror.ErrNotFound("Không tìm thấy hội thoại")
	}
	if conv.UserID != userID {
		return nil, nil, apperror.ErrForbidden("Bạn không có quyền truy cập hội thoại này")
	}

	userMsg := &Message{
		ConversationID: conversationID,
		Sender:         SenderUser,
		Content:        content,
	}
	if err := s.messages.Create(ctx, userMsg); err != nil {
		return nil, nil, apperror.ErrInternal("Không thể lưu câu hỏi", err.Error())
	}

	startedAt := time.Now()
	aiResult, aiErr := s.ai.Retrieve(ctx, content)
	responseTimeMs := int(time.Since(startedAt).Milliseconds())

	if aiErr != nil {
		botMsg := &Message{
			ConversationID: conversationID,
			Sender:         SenderBot,
			Content:        "Xin lỗi, hệ thống tra cứu pháp lý đang tạm thời không khả dụng. Vui lòng thử lại sau ít phút.",
			Metadata:       JSONMap{"responseTimeMs": responseTimeMs},
		}
		_ = s.messages.Create(ctx, botMsg)
		_ = s.conversations.Touch(ctx, conversationID)
		return userMsg, botMsg, apperror.ErrBadGateway("Không thể kết nối tới dịch vụ AI", aiErr.Error())
	}

	botMsg := &Message{
		ConversationID:     conversationID,
		Sender:             SenderBot,
		Content:            buildBotContent(aiResult),
		ExtractedHierarchy: normalizeMap(aiResult.ExtractedHierarchy),
		RelatedNodes:       normalizeSlice(aiResult.RelatedNodes),
		Metadata: JSONMap{
			"responseTimeMs":   responseTimeMs,
			"relatedDocuments": aiResult.RelatedDocuments,
			"relationships":    aiResult.Relationships,
			"nodeInformation":  aiResult.NodeInformation,
		},
	}
	if err := s.messages.Create(ctx, botMsg); err != nil {
		return nil, nil, apperror.ErrInternal("Không thể lưu câu trả lời", err.Error())
	}

	_ = s.conversations.Touch(ctx, conversationID)
	return userMsg, botMsg, nil
}

func buildBotContent(result *aiclient.RetrievalResult) string {
	if len(result.RelatedNodes) == 0 {
		return "Tôi đã tìm kiếm trong cơ sở dữ liệu pháp luật nhưng chưa tìm thấy điều khoản trực tiếp liên quan đến câu hỏi của bạn. Bạn vui lòng cung cấp thêm ngữ cảnh hoặc chi tiết cụ thể hơn."
	}
	count := len(result.RelatedNodes)
	return fmt.Sprintf("Hệ thống đã tra cứu và tìm thấy %d điều khoản/quy định pháp luật liên quan tới câu hỏi của bạn. Vui lòng xem chi tiết các trích dẫn pháp lý đính kèm.", count)
}

func normalizeMap(m map[string]any) JSONMap {
	if m == nil {
		return JSONMap{}
	}
	return JSONMap(m)
}

func normalizeSlice(s []any) []any {
	if s == nil {
		return []any{}
	}
	return s
}
