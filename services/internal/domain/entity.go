// Package domain định nghĩa entity nghiệp vụ, interface repository và lỗi nghiệp vụ.
package domain

import (
	"time"

	"github.com/google/uuid"
)

// Role biểu diễn quyền của người dùng trong hệ thống.
type Role string

const (
	// RoleUser là người dùng thường.
	RoleUser Role = "user"
	// RoleAdmin là quản trị viên, được truy cập nhóm endpoint /admin.
	RoleAdmin Role = "admin"
)

// IsValid kiểm tra giá trị role có nằm trong tập hợp cho phép.
func (r Role) IsValid() bool {
	return r == RoleUser || r == RoleAdmin
}

// Sender biểu diễn nguồn gửi của một message trong hội thoại.
type Sender string

const (
	// SenderUser là message do người dùng gửi.
	SenderUser Sender = "user"
	// SenderBot là message do hệ thống/AI trả lời.
	SenderBot Sender = "bot"
)

// User là entity người dùng lưu trong bảng `users`.
type User struct {
	ID           uuid.UUID  `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
	Email        string     `gorm:"type:varchar(255);uniqueIndex;not null"`
	Username     string     `gorm:"type:varchar(50);uniqueIndex;not null"`
	PasswordHash string     `gorm:"type:varchar(255);not null"`
	FullName     *string    `gorm:"type:varchar(255)"`
	AvatarURL    *string    `gorm:"type:text"`
	Role         Role       `gorm:"type:varchar(20);not null;default:'user'"`
	IsActive     bool       `gorm:"not null;default:true"`
	CreatedAt    time.Time  `gorm:"type:timestamptz;not null;autoCreateTime"`
	UpdatedAt    time.Time  `gorm:"type:timestamptz;not null;autoUpdateTime"`
	DeletedAt    *time.Time `gorm:"index"`
}

// TableName ghi đè tên bảng mặc định của GORM.
func (User) TableName() string {
	return "users"
}

// Conversation là entity hội thoại lưu trong bảng `conversations`.
type Conversation struct {
	ID        uuid.UUID `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
	UserID    uuid.UUID `gorm:"type:uuid;not null;index"`
	Title     string    `gorm:"type:varchar(255);not null;default:'Cuộc trò chuyện mới'"`
	CreatedAt time.Time `gorm:"type:timestamptz;not null;autoCreateTime"`
	UpdatedAt time.Time `gorm:"type:timestamptz;not null;autoUpdateTime"`

	User *User `gorm:"foreignKey:UserID;references:ID;constraint:OnDelete:CASCADE"`
}

// TableName ghi đè tên bảng mặc định của GORM.
func (Conversation) TableName() string {
	return "conversations"
}

// JSONMap là alias cho dữ liệu JSONB (nullable) của message.
type JSONMap map[string]any

// Message là entity tin nhắn lưu trong bảng `messages`.
type Message struct {
	ID                 uuid.UUID `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
	ConversationID     uuid.UUID `gorm:"type:uuid;not null;index"`
	Sender             Sender    `gorm:"type:varchar(10);not null"`
	Content            string    `gorm:"type:text;not null"`
	ExtractedHierarchy JSONMap   `gorm:"type:jsonb;serializer:json"`
	RelatedNodes       []any     `gorm:"type:jsonb;serializer:json"`
	Metadata           JSONMap   `gorm:"type:jsonb;serializer:json"`
	CreatedAt          time.Time `gorm:"type:timestamptz;not null;autoCreateTime"`

	Conversation *Conversation `gorm:"foreignKey:ConversationID;references:ID;constraint:OnDelete:CASCADE"`
}

// TableName ghi đè tên bảng mặc định của GORM.
func (Message) TableName() string {
	return "messages"
}

// Pagination mô tả thông tin phân trang trả về cho client.
type Pagination struct {
	Total      int64
	Page       int
	Limit      int
	TotalPages int
}

// PaginationParams là tham số phân trang cho truy vấn danh sách.
type PaginationParams struct {
	Page  int
	Limit int
}

// Offset tính offset bản ghi cho truy vấn SQL.
func (p PaginationParams) Offset() int {
	if p.Page < 1 {
		return 0
	}
	return (p.Page - 1) * p.Limit
}
