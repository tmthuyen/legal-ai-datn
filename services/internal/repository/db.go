// Package repository cài đặt tầng truy cập dữ liệu bằng GORM trên PostgreSQL.
package repository

import (
	"fmt"
	"log"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	"github.com/legalai/services/internal/domain"
	"github.com/legalai/services/pkg/hash"
)

// NewDB mở kết nối GORM tới PostgreSQL với DSN cho trước.
// Hàm chỉ được gọi lúc runtime (trong main), không gọi ở init để `go build` độc lập với DB.
func NewDB(dsn string, ginMode string) (*gorm.DB, error) {
	logLevel := logger.Warn
	if ginMode == "debug" {
		logLevel = logger.Info
	}

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: logger.Default.LogMode(logLevel),
	})
	if err != nil {
		return nil, fmt.Errorf("kết nối PostgreSQL thất bại: %w", err)
	}
	return db, nil
}

// Migrate chạy AutoMigrate cho 3 model User, Conversation, Message.
func Migrate(db *gorm.DB) error {
	if err := db.AutoMigrate(&domain.User{}, &domain.Conversation{}, &domain.Message{}); err != nil {
		return fmt.Errorf("auto-migrate thất bại: %w", err)
	}
	return nil
}

// seed db: admin account
func SeedDB(db *gorm.DB) error {

	adminEmail := "admin@gmail.com"
	password := "admin123"
	fullName := "Admin"
	hashedPassword, err := hash.Password(password)
	if err != nil {
		return fmt.Errorf("hash password thất bại: %w", err)
	}
	admin := &domain.User{
		Email:        adminEmail,
		PasswordHash: hashedPassword,
		Username:     adminEmail,
		FullName:     &fullName,
		Role:         "admin",
	}

	// check exist admin
	var count int64
	if err := db.Model(&domain.User{}).Where("email = ?", adminEmail).Count(&count).Error; err != nil {
		return fmt.Errorf("check exist admin thất bại: %w", err)
	}
	if count > 0 {
		log.Println("Admin đã tồn tại, không seed admin")
		return nil
	}

	if err := db.Create(admin).Error; err != nil {
		return fmt.Errorf("seed admin thất bại: %w", err)
	}
	return nil
}
