// Package jwt cung cấp logic ký và xác thực JSON Web Token.
package jwt

import (
	"errors"
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
)

// TokenType phân biệt loại token trong claims.
type TokenType string

const (
	// TypeAccess là access token mang thông tin xác thực/phân quyền.
	TypeAccess TokenType = "access"
	// TypeRefresh là refresh token dùng để cấp lại access token.
	TypeRefresh TokenType = "refresh"
)

// Claims chứa payload lưu trong JWT.
type Claims struct {
	UserID uuid.UUID `json:"user_id"`
	Role   string    `json:"role,omitempty"`
	Type   TokenType `json:"token_type"`
	jwt.RegisteredClaims
}

// Manager điều khiển việc sinh và kiểm tra JWT token.
type Manager struct {
	secret          []byte
	accessTTLMinute int
	refreshTTLHour  int
}

// NewManager tạo JWT Manager với secret và thời hạn xác định.
func NewManager(secret string, accessTTLMinute, refreshTTLHour int) *Manager {
	return &Manager{
		secret:          []byte(secret),
		accessTTLMinute: accessTTLMinute,
		refreshTTLHour:  refreshTTLHour,
	}
}

// GenerateAccessToken tạo access token chứa UserID và Role.
func (m *Manager) GenerateAccessToken(userID uuid.UUID, role string) (string, error) {
	now := time.Now()
	claims := Claims{
		UserID: userID,
		Role:   role,
		Type:   TypeAccess,
		RegisteredClaims: jwt.RegisteredClaims{
			Subject:   userID.String(),
			IssuedAt:  jwt.NewNumericDate(now),
			ExpiresAt: jwt.NewNumericDate(now.Add(time.Duration(m.accessTTLMinute) * time.Minute)),
		},
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	signed, err := token.SignedString(m.secret)
	if err != nil {
		return "", fmt.Errorf("ký access token thất bại: %w", err)
	}
	return signed, nil
}

// GenerateRefreshToken tạo refresh token chỉ chứa UserID.
func (m *Manager) GenerateRefreshToken(userID uuid.UUID) (string, error) {
	now := time.Now()
	claims := Claims{
		UserID: userID,
		Type:   TypeRefresh,
		RegisteredClaims: jwt.RegisteredClaims{
			Subject:   userID.String(),
			IssuedAt:  jwt.NewNumericDate(now),
			ExpiresAt: jwt.NewNumericDate(now.Add(time.Duration(m.refreshTTLHour) * time.Hour)),
		},
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	signed, err := token.SignedString(m.secret)
	if err != nil {
		return "", fmt.Errorf("ký refresh token thất bại: %w", err)
	}
	return signed, nil
}

// VerifyToken xác thực chữ ký và trích xuất claims từ token.
func (m *Manager) VerifyToken(tokenString string, expectedType TokenType) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(t *jwt.Token) (any, error) {
		if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("thuật toán ký không hợp lệ: %v", t.Header["alg"])
		}
		return m.secret, nil
	})
	if err != nil {
		return nil, fmt.Errorf("token không hợp lệ: %w", err)
	}

	claims, ok := token.Claims.(*Claims)
	if !ok || !token.Valid {
		return nil, errors.New("claims không hợp lệ")
	}

	if claims.Type != expectedType {
		return nil, fmt.Errorf("loại token không khớp: mong đợi %s, nhận được %s", expectedType, claims.Type)
	}

	return claims, nil
}

// RefreshTTLSeconds trả về thời hạn refresh token tính bằng giây.
func (m *Manager) RefreshTTLSeconds() int {
	return m.refreshTTLHour * 3600
}
