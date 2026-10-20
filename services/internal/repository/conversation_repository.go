package repository

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"

	"github.com/legalai/services/internal/domain"
)

// conversationRepository cài đặt domain.ConversationRepository bằng GORM.
type conversationRepository struct {
	db *gorm.DB
}

// NewConversationRepository tạo repository hội thoại mới.
func NewConversationRepository(db *gorm.DB) domain.ConversationRepository {
	return &conversationRepository{db: db}
}

// Create lưu hội thoại mới.
func (r *conversationRepository) Create(ctx context.Context, conversation *domain.Conversation) error {
	if err := r.db.WithContext(ctx).Create(conversation).Error; err != nil {
		return fmt.Errorf("tạo hội thoại thất bại: %w", err)
	}
	return nil
}

// FindByID tìm hội thoại theo ID; trả nil nếu không tồn tại.
func (r *conversationRepository) FindByID(ctx context.Context, id uuid.UUID) (*domain.Conversation, error) {
	var conversation domain.Conversation
	err := r.db.WithContext(ctx).First(&conversation, "id = ?", id).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, fmt.Errorf("tìm hội thoại theo ID thất bại: %w", err)
	}
	return &conversation, nil
}

// ListByUser trả về hội thoại của một người dùng (sắp xếp updatedAt giảm dần).
func (r *conversationRepository) ListByUser(ctx context.Context, userID uuid.UUID, params domain.PaginationParams) ([]domain.Conversation, int64, error) {
	query := r.db.WithContext(ctx).Model(&domain.Conversation{}).Where("user_id = ?", userID)

	var total int64
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, fmt.Errorf("đếm hội thoại thất bại: %w", err)
	}

	conversations := make([]domain.Conversation, 0)
	err := query.Order("updated_at DESC").Limit(params.Limit).Offset(params.Offset()).Find(&conversations).Error
	if err != nil {
		return nil, 0, fmt.Errorf("lấy danh sách hội thoại thất bại: %w", err)
	}
	return conversations, total, nil
}

// Delete xoá hội thoại theo ID (message liên quan bị xoá theo ràng buộc ON DELETE CASCADE).
func (r *conversationRepository) Delete(ctx context.Context, id uuid.UUID) error {
	if err := r.db.WithContext(ctx).Delete(&domain.Conversation{}, "id = ?", id).Error; err != nil {
		return fmt.Errorf("xoá hội thoại thất bại: %w", err)
	}
	return nil
}

// Touch cập nhật mốc updatedAt của hội thoại.
func (r *conversationRepository) Touch(ctx context.Context, id uuid.UUID) error {
	err := r.db.WithContext(ctx).
		Model(&domain.Conversation{}).
		Where("id = ?", id).
		Update("updated_at", time.Now().UTC()).Error
	if err != nil {
		return fmt.Errorf("cập nhật hội thoại thất bại: %w", err)
	}
	return nil
}

// Count trả về tổng số hội thoại.
func (r *conversationRepository) Count(ctx context.Context) (int64, error) {
	var total int64
	if err := r.db.WithContext(ctx).Model(&domain.Conversation{}).Count(&total).Error; err != nil {
		return 0, fmt.Errorf("đếm hội thoại thất bại: %w", err)
	}
	return total, nil
}
