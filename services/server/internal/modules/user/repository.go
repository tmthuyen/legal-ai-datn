package user

import (
	"context"
	"errors"
	"fmt"
	"strings"

	"github.com/google/uuid"
	"gorm.io/gorm"

	"server/internal/shared/pagination"
)

// Repository định nghĩa các thao tác truy xuất dữ liệu User.
type Repository interface {
	Create(ctx context.Context, user *User) error
	FindByID(ctx context.Context, id uuid.UUID) (*User, error)
	FindByUsername(ctx context.Context, username string) (*User, error)
	FindByEmail(ctx context.Context, email string) (*User, error)
	Update(ctx context.Context, user *User) error
	List(ctx context.Context, params pagination.Params, search string) ([]User, int64, error)
	Count(ctx context.Context) (int64, error)
}

type gormRepository struct {
	db *gorm.DB
}

// NewRepository tạo GORM repository cho User.
func NewRepository(db *gorm.DB) Repository {
	return &gormRepository{db: db}
}

func (r *gormRepository) Create(ctx context.Context, user *User) error {
	if err := r.db.WithContext(ctx).Create(user).Error; err != nil {
		return fmt.Errorf("tạo người dùng thất bại: %w", err)
	}
	return nil
}

func (r *gormRepository) FindByID(ctx context.Context, id uuid.UUID) (*User, error) {
	var u User
	err := r.db.WithContext(ctx).Where("id = ? AND deleted_at IS NULL", id).First(&u).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, fmt.Errorf("tìm người dùng theo ID thất bại: %w", err)
	}
	return &u, nil
}

func (r *gormRepository) FindByUsername(ctx context.Context, username string) (*User, error) {
	var u User
	err := r.db.WithContext(ctx).
		Where("LOWER(username) = LOWER(?) AND deleted_at IS NULL", strings.TrimSpace(username)).
		First(&u).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, fmt.Errorf("tìm người dùng theo username thất bại: %w", err)
	}
	return &u, nil
}

func (r *gormRepository) FindByEmail(ctx context.Context, email string) (*User, error) {
	var u User
	err := r.db.WithContext(ctx).
		Where("LOWER(email) = LOWER(?) AND deleted_at IS NULL", strings.TrimSpace(email)).
		First(&u).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, fmt.Errorf("tìm người dùng theo email thất bại: %w", err)
	}
	return &u, nil
}

func (r *gormRepository) Update(ctx context.Context, user *User) error {
	if err := r.db.WithContext(ctx).Save(user).Error; err != nil {
		return fmt.Errorf("cập nhật người dùng thất bại: %w", err)
	}
	return nil
}

func (r *gormRepository) List(ctx context.Context, params pagination.Params, search string) ([]User, int64, error) {
	var users []User
	var total int64

	query := r.db.WithContext(ctx).Model(&User{}).Where("deleted_at IS NULL")
	if trimmed := strings.TrimSpace(search); trimmed != "" {
		like := "%" + strings.ToLower(trimmed) + "%"
		query = query.Where("LOWER(email) LIKE ? OR LOWER(username) LIKE ? OR LOWER(full_name) LIKE ?", like, like, like)
	}

	if err := query.Count(&total).Error; err != nil {
		return nil, 0, fmt.Errorf("đếm người dùng thất bại: %w", err)
	}

	err := query.Order("created_at DESC").
		Offset(params.Offset()).
		Limit(params.Limit).
		Find(&users).Error
	if err != nil {
		return nil, 0, fmt.Errorf("lấy danh sách người dùng thất bại: %w", err)
	}

	return users, total, nil
}

func (r *gormRepository) Count(ctx context.Context) (int64, error) {
	var count int64
	err := r.db.WithContext(ctx).Model(&User{}).Where("deleted_at IS NULL").Count(&count).Error
	if err != nil {
		return 0, fmt.Errorf("đếm tổng người dùng thất bại: %w", err)
	}
	return count, nil
}
