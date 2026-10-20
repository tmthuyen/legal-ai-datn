package repository

import (
	"context"
	"fmt"

	"github.com/google/uuid"
	"gorm.io/gorm"

	"github.com/legalai/services/internal/domain"
)

// messageRepository cài đặt domain.MessageRepository bằng GORM.
type messageRepository struct {
	db *gorm.DB
}

// NewMessageRepository tạo repository tin nhắn mới.
func NewMessageRepository(db *gorm.DB) domain.MessageRepository {
	return &messageRepository{db: db}
}

// Create lưu tin nhắn mới.
func (r *messageRepository) Create(ctx context.Context, message *domain.Message) error {
	if err := r.db.WithContext(ctx).Create(message).Error; err != nil {
		return fmt.Errorf("tạo tin nhắn thất bại: %w", err)
	}
	return nil
}

// ListByConversation trả về tin nhắn của hội thoại (sắp xếp createdAt tăng dần).
func (r *messageRepository) ListByConversation(ctx context.Context, conversationID uuid.UUID, params domain.PaginationParams) ([]domain.Message, int64, error) {
	query := r.db.WithContext(ctx).Model(&domain.Message{}).Where("conversation_id = ?", conversationID)

	var total int64
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, fmt.Errorf("đếm tin nhắn thất bại: %w", err)
	}

	messages := make([]domain.Message, 0)
	err := query.Order("created_at ASC").Limit(params.Limit).Offset(params.Offset()).Find(&messages).Error
	if err != nil {
		return nil, 0, fmt.Errorf("lấy danh sách tin nhắn thất bại: %w", err)
	}
	return messages, total, nil
}

// CountBySender trả về số tin nhắn theo loại người gửi.
func (r *messageRepository) CountBySender(ctx context.Context, sender domain.Sender) (int64, error) {
	var total int64
	err := r.db.WithContext(ctx).Model(&domain.Message{}).Where("sender = ?", sender).Count(&total).Error
	if err != nil {
		return 0, fmt.Errorf("đếm tin nhắn theo sender thất bại: %w", err)
	}
	return total, nil
}
