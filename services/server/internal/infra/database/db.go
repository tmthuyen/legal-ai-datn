// Package database quản lý kết nối PostgreSQL, GORM, AutoMigrate và seeding.
package database

import (
	"fmt"
	"log"
	"time"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	gormlogger "gorm.io/gorm/logger"
)

// NewDB tạo kết nối GORM PostgreSQL với cấu hình connection pool chuẩn.
func NewDB(dsn string, ginMode string) (*gorm.DB, error) {
	logLevel := gormlogger.Warn
	if ginMode == "debug" {
		logLevel = gormlogger.Info
	}

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: gormlogger.Default.LogMode(logLevel),
		NowFunc: func() time.Time {
			return time.Now().UTC()
		},
	})
	if err != nil {
		return nil, fmt.Errorf("mở kết nối gorm thất bại: %w", err)
	}

	sqlDB, err := db.DB()
	if err != nil {
		return nil, fmt.Errorf("lấy generic sql.DB thất bại: %w", err)
	}

	sqlDB.SetMaxIdleConns(10)
	sqlDB.SetMaxOpenConns(50)
	sqlDB.SetConnMaxLifetime(time.Hour)

	return db, nil
}

// AutoMigrate thực hiện tự động tạo/cập nhật bảng theo các entity models.
func AutoMigrate(db *gorm.DB, dst ...any) error {
	if err := db.AutoMigrate(dst...); err != nil {
		return fmt.Errorf("automigrate thất bại: %w", err)
	}
	log.Println("[Database] AutoMigrate hoàn tất thành công")
	return nil
}
