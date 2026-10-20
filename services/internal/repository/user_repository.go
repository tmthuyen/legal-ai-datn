package repository

import (
	"context"
	"errors"
	"fmt"

	"github.com/google/uuid"
	"gorm.io/gorm"

	"github.com/legalai/services/internal/domain"
)

// userRepository cài đặt domain.UserRepository bằng GORM.
type userRepository struct {
	db *gorm.DB
}

// NewUserRepository tạo repository người dùng mới.
func NewUserRepository(db *gorm.DB) domain.UserRepository {
	return &userRepository{db: db}
}

// Create lưu người dùng mới và gán ID/thời gian do DB sinh.
func (r *userRepository) Create(ctx context.Context, user *domain.User) error {
	if err := r.db.WithContext(ctx).Create(user).Error; err != nil {
		return fmt.Errorf("tạo người dùng thất bại: %w", err)
	}
	return nil
}

// FindByID tìm người dùng theo ID; trả nil nếu không tồn tại.
func (r *userRepository) FindByID(ctx context.Context, id uuid.UUID) (*domain.User, error) {
	var user domain.User
	err := r.db.WithContext(ctx).First(&user, "id = ?", id).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, fmt.Errorf("tìm người dùng theo ID thất bại: %w", err)
	}
	return &user, nil
}

// FindByUsername tìm người dùng theo username; trả nil nếu không tồn tại.
func (r *userRepository) FindByUsername(ctx context.Context, username string) (*domain.User, error) {
	var user domain.User
	err := r.db.WithContext(ctx).First(&user, "username = ?", username).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, fmt.Errorf("tìm người dùng theo username thất bại: %w", err)
	}
	return &user, nil
}

// FindByEmail tìm người dùng theo email; trả nil nếu không tồn tại.
func (r *userRepository) FindByEmail(ctx context.Context, email string) (*domain.User, error) {
	var user domain.User
	err := r.db.WithContext(ctx).First(&user, "email = ?", email).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, fmt.Errorf("tìm người dùng theo email thất bại: %w", err)
	}
	return &user, nil
}

// Update lưu thay đổi của người dùng hiện có.
func (r *userRepository) Update(ctx context.Context, user *domain.User) error {
	if err := r.db.WithContext(ctx).Save(user).Error; err != nil {
		return fmt.Errorf("cập nhật người dùng thất bại: %w", err)
	}
	return nil
}

// List trả về danh sách người dùng phân trang, lọc theo email/username.
func (r *userRepository) List(ctx context.Context, params domain.PaginationParams, search string) ([]domain.User, int64, error) {
	query := r.db.WithContext(ctx).Model(&domain.User{})
	if search != "" {
		like := "%" + search + "%"
		query = query.Where("email ILIKE ? OR username ILIKE ?", like, like)
	}

	var total int64
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, fmt.Errorf("đếm người dùng thất bại: %w", err)
	}

	users := make([]domain.User, 0)
	err := query.Order("created_at DESC").Limit(params.Limit).Offset(params.Offset()).Find(&users).Error
	if err != nil {
		return nil, 0, fmt.Errorf("lấy danh sách người dùng thất bại: %w", err)
	}
	return users, total, nil
}

// Count trả về tổng số người dùng.
func (r *userRepository) Count(ctx context.Context) (int64, error) {
	var total int64
	if err := r.db.WithContext(ctx).Model(&domain.User{}).Count(&total).Error; err != nil {
		return 0, fmt.Errorf("đếm người dùng thất bại: %w", err)
	}
	return total, nil
}
