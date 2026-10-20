package domain

import (
	"context"

	"github.com/google/uuid"
)

// UserRepository định nghĩa các thao tác truy cập dữ liệu người dùng.
type UserRepository interface {
	// Create lưu người dùng mới và gán ID/thời gian do DB sinh.
	Create(ctx context.Context, user *User) error
	// FindByID tìm người dùng theo ID; trả nil nếu không tồn tại.
	FindByID(ctx context.Context, id uuid.UUID) (*User, error)
	// FindByUsername tìm người dùng theo username; trả nil nếu không tồn tại.
	FindByUsername(ctx context.Context, username string) (*User, error)
	// FindByEmail tìm người dùng theo email; trả nil nếu không tồn tại.
	FindByEmail(ctx context.Context, email string) (*User, error)
	// Update lưu thay đổi của người dùng hiện có.
	Update(ctx context.Context, user *User) error
	// List trả về danh sách người dùng phân trang, lọc theo email/username.
	List(ctx context.Context, params PaginationParams, search string) ([]User, int64, error)
	// Count trả về tổng số người dùng.
	Count(ctx context.Context) (int64, error)
}

// ConversationRepository định nghĩa các thao tác truy cập dữ liệu hội thoại.
type ConversationRepository interface {
	// Create lưu hội thoại mới.
	Create(ctx context.Context, conversation *Conversation) error
	// FindByID tìm hội thoại theo ID; trả nil nếu không tồn tại.
	FindByID(ctx context.Context, id uuid.UUID) (*Conversation, error)
	// ListByUser trả về hội thoại của một người dùng (sắp xếp updatedAt giảm dần).
	ListByUser(ctx context.Context, userID uuid.UUID, params PaginationParams) ([]Conversation, int64, error)
	// Delete xoá hội thoại theo ID.
	Delete(ctx context.Context, id uuid.UUID) error
	// Touch cập nhật mốc updatedAt của hội thoại.
	Touch(ctx context.Context, id uuid.UUID) error
	// Count trả về tổng số hội thoại.
	Count(ctx context.Context) (int64, error)
}

// MessageRepository định nghĩa các thao tác truy cập dữ liệu tin nhắn.
type MessageRepository interface {
	// Create lưu tin nhắn mới.
	Create(ctx context.Context, message *Message) error
	// ListByConversation trả về tin nhắn của hội thoại (sắp xếp createdAt tăng dần).
	ListByConversation(ctx context.Context, conversationID uuid.UUID, params PaginationParams) ([]Message, int64, error)
	// CountBySender trả về số tin nhắn theo loại người gửi.
	CountBySender(ctx context.Context, sender Sender) (int64, error)
}
