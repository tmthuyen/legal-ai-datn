package user

import (
	"time"

	"github.com/google/uuid"
)

// Role định nghĩa quyền của người dùng.
type Role string

const (
	RoleUser  Role = "user"
	RoleAdmin Role = "admin"
)

// IsValid kiểm tra role hợp lệ.
func (r Role) IsValid() bool {
	return r == RoleUser || r == RoleAdmin
}

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
