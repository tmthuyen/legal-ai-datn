package user

import (
	"context"
	"strings"

	"github.com/google/uuid"

	"server/internal/shared/apperror"
	"server/internal/shared/hash"
)

// Service xử lý logic nghiệp vụ người dùng.
type Service struct {
	repo Repository
}

// NewService tạo Service mới.
func NewService(repo Repository) *Service {
	return &Service{repo: repo}
}

// UpdateProfile cập nhật tên đầy đủ và avatar.
func (s *Service) UpdateProfile(ctx context.Context, userID uuid.UUID, req UpdateProfileRequest) (*User, error) {
	user, err := s.repo.FindByID(ctx, userID)
	if err != nil {
		return nil, apperror.ErrInternal("Không thể tìm người dùng", err.Error())
	}
	if user == nil {
		return nil, apperror.ErrNotFound("Không tìm thấy người dùng")
	}

	if req.FullName != nil {
		trimmed := strings.TrimSpace(*req.FullName)
		user.FullName = &trimmed
	}
	if req.AvatarURL != nil {
		trimmed := strings.TrimSpace(*req.AvatarURL)
		user.AvatarURL = &trimmed
	}

	if err := s.repo.Update(ctx, user); err != nil {
		return nil, apperror.ErrInternal("Không thể cập nhật hồ sơ", err.Error())
	}

	return user, nil
}

// ChangePassword đổi mật khẩu người dùng sau khi xác thực mật khẩu cũ.
func (s *Service) ChangePassword(ctx context.Context, userID uuid.UUID, oldPassword, newPassword string) error {
	if len([]rune(newPassword)) < 6 {
		return apperror.ErrBadRequest("Mật khẩu mới phải có ít nhất 6 ký tự")
	}

	user, err := s.repo.FindByID(ctx, userID)
	if err != nil {
		return apperror.ErrInternal("Không thể tìm người dùng", err.Error())
	}
	if user == nil {
		return apperror.ErrNotFound("Không tìm thấy người dùng")
	}

	if !hash.CheckPassword(oldPassword, user.PasswordHash) {
		return apperror.ErrBadRequest("Mật khẩu hiện tại không chính xác")
	}

	newHash, err := hash.Password(newPassword)
	if err != nil {
		return apperror.ErrInternal("Không thể băm mật khẩu mới", err.Error())
	}

	user.PasswordHash = newHash
	if err := s.repo.Update(ctx, user); err != nil {
		return apperror.ErrInternal("Không thể lưu mật khẩu mới", err.Error())
	}

	return nil
}
