package chat

import (
	"time"

	"github.com/google/uuid"
	"server/internal/modules/user"
)

// Sender biểu diễn người gửi tin nhắn trong hội thoại.
type Sender string

const (
	SenderUser Sender = "user"
	SenderBot  Sender = "bot"
)

// JSONMap alias cho dữ liệu JSONB.
type JSONMap map[string]any

// Conversation là entity hội thoại lưu trong bảng `conversations`.
type Conversation struct {
	ID        uuid.UUID  `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
	UserID    uuid.UUID  `gorm:"type:uuid;not null;index"`
	Title     string     `gorm:"type:varchar(255);not null;default:'Cuộc trò chuyện mới'"`
	CreatedAt time.Time  `gorm:"type:timestamptz;not null;autoCreateTime"`
	UpdatedAt time.Time  `gorm:"type:timestamptz;not null;autoUpdateTime"`
	DeletedAt *time.Time `gorm:"index"`

	User *user.User `gorm:"foreignKey:UserID;references:ID;constraint:OnDelete:CASCADE"`
}

// TableName ghi đè tên bảng mặc định của GORM.
func (Conversation) TableName() string {
	return "conversations"
}

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
