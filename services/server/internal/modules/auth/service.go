package auth

import (
	"context"
	"strings"

	"github.com/google/uuid"

	"server/internal/modules/user"
	"server/internal/shared/apperror"
	"server/internal/shared/hash"
	"server/internal/shared/jwt"
)

// Service điều phối đăng ký, đăng nhập và cấp phát token.
type Service struct {
	users user.Repository
	jwt   *jwt.Manager
}

// NewService tạo Service mới cho Auth.
func NewService(users user.Repository, jwtMgr *jwt.Manager) *Service {
	return &Service{
		users: users,
		jwt:   jwtMgr,
	}
}

// TokenPair chứa cặp Access Token và Refresh Token.
type TokenPair struct {
	AccessToken  string
	RefreshToken string
	User         *user.User
}

// Register tạo người dùng mới và cấp token ban đầu.
func (s *Service) Register(ctx context.Context, req RegisterRequest) (*TokenPair, error) {
	email := strings.ToLower(strings.TrimSpace(req.Email))
	username := strings.TrimSpace(req.Username)

	existing, err := s.users.FindByEmail(ctx, email)
	if err != nil {
		return nil, apperror.ErrInternal("Kiểm tra email thất bại", err.Error())
	}
	if existing != nil {
		return nil, apperror.ErrConflict("Email đã được sử dụng")
	}

	existingUser, err := s.users.FindByUsername(ctx, username)
	if err != nil {
		return nil, apperror.ErrInternal("Kiểm tra username thất bại", err.Error())
	}
	if existingUser != nil {
		return nil, apperror.ErrConflict("Tên đăng nhập đã tồn tại")
	}

	pwdHash, err := hash.Password(req.Password)
	if err != nil {
		return nil, apperror.ErrInternal("Băm mật khẩu thất bại", err.Error())
	}

	newUser := &user.User{
		Email:        email,
		Username:     username,
		PasswordHash: pwdHash,
		FullName:     req.FullName,
		Role:         user.RoleUser,
		IsActive:     true,
	}

	if err := s.users.Create(ctx, newUser); err != nil {
		return nil, apperror.ErrInternal("Không thể tạo tài khoản", err.Error())
	}

	accessToken, err := s.jwt.GenerateAccessToken(newUser.ID, string(newUser.Role))
	if err != nil {
		return nil, apperror.ErrInternal("Sinh access token thất bại", err.Error())
	}

	refreshToken, err := s.jwt.GenerateRefreshToken(newUser.ID)
	if err != nil {
		return nil, apperror.ErrInternal("Sinh refresh token thất bại", err.Error())
	}

	return &TokenPair{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		User:         newUser,
	}, nil
}

// Login xác thực thông tin đăng nhập và cấp token mới.
func (s *Service) Login(ctx context.Context, req LoginRequest) (*TokenPair, error) {
	identifier := strings.TrimSpace(req.Identifier)

	var u *user.User
	var err error

	if strings.Contains(identifier, "@") {
		u, err = s.users.FindByEmail(ctx, identifier)
	} else {
		u, err = s.users.FindByUsername(ctx, identifier)
	}

	if err != nil {
		return nil, apperror.ErrInternal("Xác thực thông tin thất bại", err.Error())
	}
	if u == nil {
		return nil, apperror.ErrUnauthorized("Tên đăng nhập hoặc mật khẩu không chính xác")
	}

	if !u.IsActive {
		return nil, apperror.ErrForbidden("Tài khoản của bạn đã bị vô hiệu hoá")
	}

	if !hash.CheckPassword(req.Password, u.PasswordHash) {
		return nil, apperror.ErrUnauthorized("Tên đăng nhập hoặc mật khẩu không chính xác")
	}

	accessToken, err := s.jwt.GenerateAccessToken(u.ID, string(u.Role))
	if err != nil {
		return nil, apperror.ErrInternal("Sinh access token thất bại", err.Error())
	}

	refreshToken, err := s.jwt.GenerateRefreshToken(u.ID)
	if err != nil {
		return nil, apperror.ErrInternal("Sinh refresh token thất bại", err.Error())
	}

	return &TokenPair{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		User:         u,
	}, nil
}

// RefreshToken xác thực refresh token và cấp access token mới.
func (s *Service) RefreshToken(ctx context.Context, refreshTokenString string) (string, error) {
	claims, err := s.jwt.VerifyToken(refreshTokenString, jwt.TypeRefresh)
	if err != nil {
		return "", apperror.ErrUnauthorized("Refresh token không hợp lệ hoặc đã hết hạn")
	}

	u, err := s.users.FindByID(ctx, claims.UserID)
	if err != nil {
		return "", apperror.ErrInternal("Kiểm tra thông tin người dùng thất bại", err.Error())
	}
	if u == nil || !u.IsActive {
		return "", apperror.ErrUnauthorized("Tài khoản không tồn tại hoặc đã bị khoá")
	}

	accessToken, err := s.jwt.GenerateAccessToken(u.ID, string(u.Role))
	if err != nil {
		return "", apperror.ErrInternal("Sinh access token thất bại", err.Error())
	}

	return accessToken, nil
}

// GetCurrentUser lấy thông tin người dùng hiện tại qua ID.
func (s *Service) GetCurrentUser(ctx context.Context, userID uuid.UUID) (*user.User, error) {
	u, err := s.users.FindByID(ctx, userID)
	if err != nil {
		return nil, apperror.ErrInternal("Lấy thông tin người dùng thất bại", err.Error())
	}
	if u == nil {
		return nil, apperror.ErrNotFound("Không tìm thấy người dùng")
	}
	return u, nil
}
