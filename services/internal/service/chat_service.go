package service

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"

	"github.com/legalai/services/internal/aiclient"
	"github.com/legalai/services/internal/domain"
)

// ChatService xử lý hội thoại, tin nhắn và làm AI Gateway trung chuyển sang Backend.
type ChatService struct {
	conversations domain.ConversationRepository
	messages      domain.MessageRepository
	ai            *aiclient.Client
}

// NewChatService tạo ChatService mới.
func NewChatService(
	conversations domain.ConversationRepository,
	messages domain.MessageRepository,
	ai *aiclient.Client,
) *ChatService {
	return &ChatService{conversations: conversations, messages: messages, ai: ai}
}

// ChatReply là kết quả một lượt hỏi đáp (message user + message bot).
type ChatReply struct {
	UserMessage *domain.Message
	BotMessage  *domain.Message
}

// defaultConversationTitle là tiêu đề mặc định khi client không truyền.
const defaultConversationTitle = "Cuộc trò chuyện mới"

// ListConversations trả danh sách hội thoại của người dùng (phân trang).
func (s *ChatService) ListConversations(ctx context.Context, userID uuid.UUID, params domain.PaginationParams) ([]domain.Conversation, *domain.Pagination, error) {
	conversations, total, err := s.conversations.ListByUser(ctx, userID, params)
	if err != nil {
		return nil, nil, domain.ErrInternal("Không thể lấy danh sách hội thoại", err.Error())
	}
	return conversations, buildPagination(total, params), nil
}

// CreateConversation tạo hội thoại mới cho người dùng.
func (s *ChatService) CreateConversation(ctx context.Context, userID uuid.UUID, title string) (*domain.Conversation, error) {
	title = strings.TrimSpace(title)
	if title == "" {
		title = defaultConversationTitle
	}
	if len([]rune(title)) > 255 {
		return nil, domain.ErrBadRequest("Tiêu đề hội thoại tối đa 255 ký tự")
	}

	conversation := &domain.Conversation{
		UserID: userID,
		Title:  title,
	}
	if err := s.conversations.Create(ctx, conversation); err != nil {
		return nil, domain.ErrInternal("Không thể tạo hội thoại", err.Error())
	}
	return conversation, nil
}

// DeleteConversation xoá hội thoại; 404 nếu không tồn tại, 403 nếu không phải chủ.
func (s *ChatService) DeleteConversation(ctx context.Context, userID, conversationID uuid.UUID) error {
	conversation, err := s.conversations.FindByID(ctx, conversationID)
	if err != nil {
		return domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	if conversation == nil {
		return domain.ErrNotFound("Không tìm thấy hội thoại")
	}
	if conversation.UserID != userID {
		return domain.ErrForbidden("Bạn không có quyền truy cập hội thoại này")
	}
	if err := s.conversations.Delete(ctx, conversationID); err != nil {
		return domain.ErrInternal("Không thể xoá hội thoại", err.Error())
	}
	return nil
}

// ListMessages trả tin nhắn của hội thoại (phân trang, createdAt tăng dần).
func (s *ChatService) ListMessages(ctx context.Context, userID, conversationID uuid.UUID, params domain.PaginationParams) ([]domain.Message, *domain.Pagination, error) {
	conversation, err := s.conversations.FindByID(ctx, conversationID)
	if err != nil {
		return nil, nil, domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	if conversation == nil {
		return nil, nil, domain.ErrNotFound("Không tìm thấy hội thoại")
	}
	if conversation.UserID != userID {
		return nil, nil, domain.ErrForbidden("Bạn không có quyền truy cập hội thoại này")
	}

	messages, total, err := s.messages.ListByConversation(ctx, conversationID, params)
	if err != nil {
		return nil, nil, domain.ErrInternal("Không thể lấy danh sách tin nhắn", err.Error())
	}
	return messages, buildPagination(total, params), nil
}

// SendMessage lưu câu hỏi của user, gọi Backend AI, lưu câu trả lời của bot và trả cả hai.
// Nếu Backend lỗi/không phản hồi, vẫn lưu bot message thân thiện và trả lỗi 502.
func (s *ChatService) SendMessage(ctx context.Context, userID, conversationID uuid.UUID, content string) (*ChatReply, error) {
	content = strings.TrimSpace(content)
	if content == "" {
		return nil, domain.ErrBadRequest("Nội dung câu hỏi là bắt buộc")
	}

	conversation, err := s.conversations.FindByID(ctx, conversationID)
	if err != nil {
		return nil, domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	if conversation == nil {
		return nil, domain.ErrNotFound("Không tìm thấy hội thoại")
	}
	if conversation.UserID != userID {
		return nil, domain.ErrForbidden("Bạn không có quyền truy cập hội thoại này")
	}

	userMessage := &domain.Message{
		ConversationID: conversationID,
		Sender:         domain.SenderUser,
		Content:        content,
	}
	if err := s.messages.Create(ctx, userMessage); err != nil {
		return nil, domain.ErrInternal("Không thể lưu câu hỏi", err.Error())
	}

	startedAt := time.Now()
	result, aiErr := s.ai.Retrieve(ctx, content)
	responseTimeMs := int(time.Since(startedAt).Milliseconds())

	if aiErr != nil {
		botMessage := &domain.Message{
			ConversationID: conversationID,
			Sender:         domain.SenderBot,
			Content:        "Xin lỗi, hệ thống tra cứu pháp lý đang tạm thời không khả dụng. Vui lòng thử lại sau ít phút.",
			Metadata:       domain.JSONMap{"responseTimeMs": responseTimeMs},
		}
		if createErr := s.messages.Create(ctx, botMessage); createErr != nil {
			return nil, domain.ErrInternal("Không thể lưu câu trả lời", createErr.Error())
		}
		if touchErr := s.conversations.Touch(ctx, conversationID); touchErr != nil {
			return nil, domain.ErrInternal("Không thể cập nhật hội thoại", touchErr.Error())
		}
		return &ChatReply{UserMessage: userMessage, BotMessage: botMessage},
			domain.ErrBadGateway("Không thể kết nối tới dịch vụ AI", aiErr.Error())
	}

	botMessage := &domain.Message{
		ConversationID:     conversationID,
		Sender:             domain.SenderBot,
		Content:            buildBotContent(result),
		ExtractedHierarchy: normalizeMap(result.ExtractedHierarchy),
		RelatedNodes:       normalizeSlice(result.RelatedNodes),
		Metadata:           domain.JSONMap{"responseTimeMs": responseTimeMs},
	}
	if err := s.messages.Create(ctx, botMessage); err != nil {
		return nil, domain.ErrInternal("Không thể lưu câu trả lời", err.Error())
	}
	if err := s.conversations.Touch(ctx, conversationID); err != nil {
		return nil, domain.ErrInternal("Không thể cập nhật hội thoại", err.Error())
	}

	return &ChatReply{UserMessage: userMessage, BotMessage: botMessage}, nil
}

// buildBotContent tổng hợp nội dung trả lời của bot từ `related_nodes`.
// Hỗ trợ các key phổ biến của Backend: text/content/title + citation/node_id.
func buildBotContent(result *aiclient.RetrievalResult) string {
	if result == nil || len(result.RelatedNodes) == 0 {
		return "Không tìm thấy quy định liên quan trong cơ sở dữ liệu pháp luật hiện có."
	}

	var builder strings.Builder
	builder.WriteString("Dựa trên cơ sở dữ liệu pháp luật, tôi tìm thấy các quy định liên quan sau:\n")
	for index, rawNode := range result.RelatedNodes {
		node, ok := rawNode.(map[string]any)
		if !ok {
			continue
		}

		citation := firstString(node, "citation", "node_id", "title", "number")
		text := firstString(node, "text", "content", "full_text", "title")

		if citation == "" && text == "" {
			continue
		}
		builder.WriteString(fmt.Sprintf("\n%d. ", index+1))
		if citation != "" {
			builder.WriteString(citation)
			if text != "" {
				builder.WriteString(": ")
			}
		}
		if text != "" {
			builder.WriteString(text)
		}
	}

	content := strings.TrimSpace(builder.String())
	if content == "Dựa trên cơ sở dữ liệu pháp luật, tôi tìm thấy các quy định liên quan sau:" {
		return "Không tìm thấy quy định liên quan trong cơ sở dữ liệu pháp luật hiện có."
	}
	return content
}

// firstString trả về giá trị chuỗi không rỗng đầu tiên theo thứ tự key.
func firstString(node map[string]any, keys ...string) string {
	for _, key := range keys {
		value, ok := node[key]
		if !ok {
			continue
		}
		if text, ok := value.(string); ok && strings.TrimSpace(text) != "" {
			return strings.TrimSpace(text)
		}
	}
	return ""
}

// normalizeMap trả nil nếu map rỗng để cột jsonb lưu NULL đúng contract.
func normalizeMap(value map[string]any) domain.JSONMap {
	if len(value) == 0 {
		return nil
	}
	return domain.JSONMap(value)
}

// normalizeSlice trả nil nếu slice rỗng để cột jsonb lưu NULL đúng contract.
func normalizeSlice(value []any) []any {
	if len(value) == 0 {
		return nil
	}
	return value
}

// buildPagination dựng thông tin phân trang từ tổng số bản ghi và tham số truy vấn.
func buildPagination(total int64, params domain.PaginationParams) *domain.Pagination {
	limit := params.Limit
	if limit < 1 {
		limit = 1
	}
	page := params.Page
	if page < 1 {
		page = 1
	}
	totalPages := int((total + int64(limit) - 1) / int64(limit))
	return &domain.Pagination{
		Total:      total,
		Page:       page,
		Limit:      limit,
		TotalPages: totalPages,
	}
}
