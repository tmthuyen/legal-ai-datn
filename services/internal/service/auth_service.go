// Package service chứa logic nghiệp vụ của Services.
package service

import (
	"context"
	"errors"
	"strings"

	"github.com/google/uuid"
	"gorm.io/gorm"

	"github.com/legalai/services/internal/domain"
	"github.com/legalai/services/pkg/hash"
	"github.com/legalai/services/pkg/jwt"
)

// AuthService xử lý đăng ký, đăng nhập, refresh và truy vấn người dùng hiện tại.
type AuthService struct {
	users domain.UserRepository
	jwt   *jwt.Manager
}

// NewAuthService tạo AuthService mới.
func NewAuthService(users domain.UserRepository, jwtManager *jwt.Manager) *AuthService {
	return &AuthService{users: users, jwt: jwtManager}
}

// RegisterInput là dữ liệu đầu vào cho đăng ký.
type RegisterInput struct {
	Email    string
	Username string
	Password string
	FullName string
}

// AuthResult là kết quả trả về cho Frontend (accessToken + user).
type AuthResult struct {
	AccessToken string
	User        *domain.User
}

// TokenPair gồm access token (trả body) và refresh token (set cookie).
type TokenPair struct {
	AccessToken  string
	RefreshToken string
}

// Register tạo người dùng mới, trả cặp token.
// Lỗi 409 nếu email/username đã tồn tại; 400/422 nếu dữ liệu không hợp lệ.
func (s *AuthService) Register(ctx context.Context, input RegisterInput) (*AuthResult, *TokenPair, error) {
	email := strings.TrimSpace(strings.ToLower(input.Email))
	username := strings.TrimSpace(input.Username)
	fullName := strings.TrimSpace(input.FullName)

	if email == "" {
		return nil, nil, domain.ErrUnprocessable("Dữ liệu không hợp lệ", "email là bắt buộc")
	}
	if !strings.Contains(email, "@") {
		return nil, nil, domain.ErrUnprocessable("Dữ liệu không hợp lệ", "email không đúng định dạng")
	}
	if len(username) < 3 || len(username) > 50 {
		return nil, nil, domain.ErrUnprocessable("Dữ liệu không hợp lệ", "username phải từ 3 đến 50 ký tự")
	}
	if len(input.Password) < 8 {
		return nil, nil, domain.ErrUnprocessable("Dữ liệu không hợp lệ", "password phải có tối thiểu 8 ký tự")
	}

	existingEmail, err := s.users.FindByEmail(ctx, email)
	if err != nil {
		return nil, nil, domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	if existingEmail != nil {
		return nil, nil, domain.ErrConflict("Email đã được sử dụng")
	}

	existingUsername, err := s.users.FindByUsername(ctx, username)
	if err != nil {
		return nil, nil, domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	if existingUsername != nil {
		return nil, nil, domain.ErrConflict("Username đã được sử dụng")
	}

	passwordHash, err := hash.Password(input.Password)
	if err != nil {
		return nil, nil, domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}

	user := &domain.User{
		Email:        email,
		Username:     username,
		PasswordHash: passwordHash,
		Role:         domain.RoleUser,
		IsActive:     true,
	}
	if fullName != "" {
		user.FullName = &fullName
	}

	if err := s.users.Create(ctx, user); err != nil {
		if isUniqueViolation(err) {
			return nil, nil, domain.ErrConflict("Email hoặc username đã được sử dụng")
		}
		return nil, nil, domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}

	return s.issueTokens(user)
}

// Login xác thực username/password, trả cặp token. Lỗi 401 nếu sai thông tin.
func (s *AuthService) Login(ctx context.Context, username, password string) (*AuthResult, *TokenPair, error) {
	user, err := s.users.FindByUsername(ctx, strings.TrimSpace(username))
	if err != nil {
		return nil, nil, domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	if user == nil {
		return nil, nil, domain.ErrUnauthorized("Thông tin đăng nhập không chính xác")
	}
	if err := hash.Verify(user.PasswordHash, password); err != nil {
		return nil, nil, domain.ErrUnauthorized("Thông tin đăng nhập không chính xác")
	}
	if !user.IsActive {
		return nil, nil, domain.ErrForbidden("Tài khoản đã bị khoá")
	}

	return s.issueTokens(user)
}

// Refresh xác thực refresh token và cấp access token mới. Lỗi 401 nếu token sai/hết hạn.
func (s *AuthService) Refresh(ctx context.Context, refreshToken string) (string, error) {
	if strings.TrimSpace(refreshToken) == "" {
		return "", domain.ErrUnauthorized("Thiếu refresh token")
	}

	claims, err := s.jwt.ParseRefresh(refreshToken)
	if err != nil {
		return "", domain.ErrUnauthorized("Refresh token không hợp lệ hoặc đã hết hạn")
	}

	user, err := s.users.FindByID(ctx, claims.UserID)
	if err != nil {
		return "", domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	if user == nil || !user.IsActive {
		return "", domain.ErrUnauthorized("Tài khoản không khả dụng")
	}

	accessToken, err := s.jwt.GenerateAccess(user.ID, string(user.Role))
	if err != nil {
		return "", domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	return accessToken, nil
}

// Me trả thông tin người dùng theo ID trong access token.
func (s *AuthService) Me(ctx context.Context, userID uuid.UUID) (*domain.User, error) {
	user, err := s.users.FindByID(ctx, userID)
	if err != nil {
		return nil, domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	if user == nil {
		return nil, domain.ErrNotFound("Không tìm thấy người dùng")
	}
	return user, nil
}

// issueTokens sinh access/refresh token và đóng gói kết quả.
func (s *AuthService) issueTokens(user *domain.User) (*AuthResult, *TokenPair, error) {
	accessToken, err := s.jwt.GenerateAccess(user.ID, string(user.Role))
	if err != nil {
		return nil, nil, domain.ErrInternal("Không thể tạo token", err.Error())
	}
	refreshToken, err := s.jwt.GenerateRefresh(user.ID, string(user.Role))
	if err != nil {
		return nil, nil, domain.ErrInternal("Không thể tạo token", err.Error())
	}
	return &AuthResult{AccessToken: accessToken, User: user}, &TokenPair{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
	}, nil
}

// isUniqueViolation nhận diện lỗi vi phạm ràng buộc unique của PostgreSQL.
func isUniqueViolation(err error) bool {
	if err == nil {
		return false
	}
	if errors.Is(err, gorm.ErrDuplicatedKey) {
		return true
	}
	message := strings.ToLower(err.Error())
	return strings.Contains(message, "duplicate key") || strings.Contains(message, "unique constraint")
}
