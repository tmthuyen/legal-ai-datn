package database

import (
	"context"
	"fmt"
	"log"

	"gorm.io/gorm"

	"server/internal/modules/user"
	"server/internal/shared/hash"
)

// SeedData tạo sẵn tài khoản Admin và User mẫu nếu cơ sở dữ liệu còn rỗng.
func SeedData(db *gorm.DB) error {
	ctx := context.Background()

	var count int64
	if err := db.WithContext(ctx).Model(&user.User{}).Count(&count).Error; err != nil {
		return fmt.Errorf("kiểm tra dữ liệu user thất bại: %w", err)
	}
	if count > 0 {
		return nil
	}

	log.Println("[Database] Đang khởi tạo tài khoản mặc định (Admin & User)...")

	adminPassword, err := hash.Password("Admin@123456")
	if err != nil {
		return err
	}
	userPassword, err := hash.Password("User@123456")
	if err != nil {
		return err
	}

	adminFullName := "Quản trị viên Hệ thống"
	userFullName := "Người dùng Mẫu"

	users := []user.User{
		{
			Email:        "admin@legalai.vn",
			Username:     "admin",
			PasswordHash: adminPassword,
			FullName:     &adminFullName,
			Role:         user.RoleAdmin,
			IsActive:     true,
		},
		{
			Email:        "user@legalai.vn",
			Username:     "user",
			PasswordHash: userPassword,
			FullName:     &userFullName,
			Role:         user.RoleUser,
			IsActive:     true,
		},
	}

	if err := db.WithContext(ctx).Create(&users).Error; err != nil {
		return fmt.Errorf("seed users thất bại: %w", err)
	}

	log.Println("[Database] Khởi tạo tài khoản mẫu thành công (admin@legalai.vn / user@legalai.vn)")
	return nil
}
