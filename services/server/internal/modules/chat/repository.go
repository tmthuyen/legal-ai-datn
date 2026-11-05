package chat

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"

	"server/internal/shared/pagination"
)

// ConversationRepository định nghĩa truy xuất dữ liệu hội thoại.
type ConversationRepository interface {
	Create(ctx context.Context, conversation *Conversation) error
	FindByID(ctx context.Context, id uuid.UUID) (*Conversation, error)
	ListByUser(ctx context.Context, userID uuid.UUID, params pagination.Params) ([]Conversation, int64, error)
	Delete(ctx context.Context, id uuid.UUID) error
	Touch(ctx context.Context, id uuid.UUID) error
	Count(ctx context.Context) (int64, error)
}

// MessageRepository định nghĩa truy xuất dữ liệu tin nhắn.
type MessageRepository interface {
	Create(ctx context.Context, message *Message) error
	ListByConversation(ctx context.Context, conversationID uuid.UUID, params pagination.Params) ([]Message, int64, error)
	CountBySender(ctx context.Context, sender Sender) (int64, error)
	Count(ctx context.Context) (int64, error)
}

type gormConversationRepo struct {
	db *gorm.DB
}

// NewConversationRepository tạo GORM repository cho hội thoại.
func NewConversationRepository(db *gorm.DB) ConversationRepository {
	return &gormConversationRepo{db: db}
}

func (r *gormConversationRepo) Create(ctx context.Context, conversation *Conversation) error {
	if err := r.db.WithContext(ctx).Create(conversation).Error; err != nil {
		return fmt.Errorf("tạo hội thoại thất bại: %w", err)
	}
	return nil
}

func (r *gormConversationRepo) FindByID(ctx context.Context, id uuid.UUID) (*Conversation, error) {
	var c Conversation
	err := r.db.WithContext(ctx).Where("id = ? AND deleted_at IS NULL", id).First(&c).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, fmt.Errorf("tìm hội thoại thất bại: %w", err)
	}
	return &c, nil
}

func (r *gormConversationRepo) ListByUser(ctx context.Context, userID uuid.UUID, params pagination.Params) ([]Conversation, int64, error) {
	var conversations []Conversation
	var total int64

	query := r.db.WithContext(ctx).Model(&Conversation{}).Where("user_id = ? AND deleted_at IS NULL", userID)
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, fmt.Errorf("đếm hội thoại thất bại: %w", err)
	}

	err := query.Order("updated_at DESC").
		Offset(params.Offset()).
		Limit(params.Limit).
		Find(&conversations).Error
	if err != nil {
		return nil, 0, fmt.Errorf("lấy danh sách hội thoại thất bại: %w", err)
	}

	return conversations, total, nil
}

func (r *gormConversationRepo) Delete(ctx context.Context, id uuid.UUID) error {
	now := time.Now().UTC()
	err := r.db.WithContext(ctx).Model(&Conversation{}).
		Where("id = ? AND deleted_at IS NULL", id).
		Update("deleted_at", now).Error
	if err != nil {
		return fmt.Errorf("xoá hội thoại thất bại: %w", err)
	}
	return nil
}

func (r *gormConversationRepo) Touch(ctx context.Context, id uuid.UUID) error {
	now := time.Now().UTC()
	err := r.db.WithContext(ctx).Model(&Conversation{}).
		Where("id = ?", id).
		Update("updated_at", now).Error
	if err != nil {
		return fmt.Errorf("cập nhật updated_at hội thoại thất bại: %w", err)
	}
	return nil
}

func (r *gormConversationRepo) Count(ctx context.Context) (int64, error) {
	var count int64
	err := r.db.WithContext(ctx).Model(&Conversation{}).Where("deleted_at IS NULL").Count(&count).Error
	if err != nil {
		return 0, fmt.Errorf("đếm tổng hội thoại thất bại: %w", err)
	}
	return count, nil
}

type gormMessageRepo struct {
	db *gorm.DB
}

// NewMessageRepository tạo GORM repository cho tin nhắn.
func NewMessageRepository(db *gorm.DB) MessageRepository {
	return &gormMessageRepo{db: db}
}

func (r *gormMessageRepo) Create(ctx context.Context, message *Message) error {
	if err := r.db.WithContext(ctx).Create(message).Error; err != nil {
		return fmt.Errorf("lưu tin nhắn thất bại: %w", err)
	}
	return nil
}

func (r *gormMessageRepo) ListByConversation(ctx context.Context, conversationID uuid.UUID, params pagination.Params) ([]Message, int64, error) {
	var messages []Message
	var total int64

	query := r.db.WithContext(ctx).Model(&Message{}).Where("conversation_id = ?", conversationID)
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, fmt.Errorf("đếm tin nhắn thất bại: %w", err)
	}

	err := query.Order("created_at ASC").
		Offset(params.Offset()).
		Limit(params.Limit).
		Find(&messages).Error
	if err != nil {
		return nil, 0, fmt.Errorf("lấy danh sách tin nhắn thất bại: %w", err)
	}

	return messages, total, nil
}

func (r *gormMessageRepo) CountBySender(ctx context.Context, sender Sender) (int64, error) {
	var count int64
	err := r.db.WithContext(ctx).Model(&Message{}).Where("sender = ?", sender).Count(&count).Error
	if err != nil {
		return 0, fmt.Errorf("đếm tin nhắn theo sender thất bại: %w", err)
	}
	return count, nil
}

func (r *gormMessageRepo) Count(ctx context.Context) (int64, error) {
	var count int64
	err := r.db.WithContext(ctx).Model(&Message{}).Count(&count).Error
	if err != nil {
		return 0, fmt.Errorf("đếm tổng tin nhắn thất bại: %w", err)
	}
	return count, nil
}
