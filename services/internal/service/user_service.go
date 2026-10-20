package service

import (
	"context"
	"strings"

	"github.com/google/uuid"

	"github.com/legalai/services/internal/domain"
	"github.com/legalai/services/pkg/hash"
)

// UserService xử lý nghiệp vụ hồ sơ cá nhân và đổi mật khẩu.
type UserService struct {
	users domain.UserRepository
}

// NewUserService tạo UserService mới.
func NewUserService(users domain.UserRepository) *UserService {
	return &UserService{users: users}
}

// UpdateProfileInput là dữ liệu cập nhật hồ sơ (mọi trường tùy chọn).
type UpdateProfileInput struct {
	FullName  *string
	AvatarURL *string
}

// UpdateProfile cập nhật hồ sơ người dùng; yêu cầu ít nhất 1 trường.
func (s *UserService) UpdateProfile(ctx context.Context, userID uuid.UUID, input UpdateProfileInput) (*domain.User, error) {
	if input.FullName == nil && input.AvatarURL == nil {
		return nil, domain.ErrBadRequest("Cần cung cấp ít nhất một trường để cập nhật")
	}

	user, err := s.users.FindByID(ctx, userID)
	if err != nil {
		return nil, domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	if user == nil {
		return nil, domain.ErrNotFound("Không tìm thấy người dùng")
	}

	if input.FullName != nil {
		fullName := strings.TrimSpace(*input.FullName)
		user.FullName = &fullName
	}
	if input.AvatarURL != nil {
		avatarURL := strings.TrimSpace(*input.AvatarURL)
		user.AvatarURL = &avatarURL
	}

	if err := s.users.Update(ctx, user); err != nil {
		return nil, domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	return user, nil
}

// ChangePassword đổi mật khẩu người dùng; lỗi 400 nếu oldPassword sai.
func (s *UserService) ChangePassword(ctx context.Context, userID uuid.UUID, oldPassword, newPassword string) error {
	if strings.TrimSpace(oldPassword) == "" || strings.TrimSpace(newPassword) == "" {
		return domain.ErrBadRequest("Mật khẩu cũ và mật khẩu mới là bắt buộc")
	}
	if len(newPassword) < 8 {
		return domain.ErrBadRequest("Mật khẩu mới phải có tối thiểu 8 ký tự")
	}

	user, err := s.users.FindByID(ctx, userID)
	if err != nil {
		return domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	if user == nil {
		return domain.ErrNotFound("Không tìm thấy người dùng")
	}

	if err := hash.Verify(user.PasswordHash, oldPassword); err != nil {
		return domain.ErrBadRequest("Mật khẩu cũ không chính xác")
	}

	newHash, err := hash.Password(newPassword)
	if err != nil {
		return domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	user.PasswordHash = newHash

	if err := s.users.Update(ctx, user); err != nil {
		return domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	return nil
}
