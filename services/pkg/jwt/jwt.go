// Package jwt cung cấp hàm ký và xác thực JWT (HS256) cho access/refresh token.
package jwt

import (
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
)

// TokenType phân biệt loại token trong claim.
type TokenType string

const (
	// TypeAccess là token dùng cho header Authorization.
	TypeAccess TokenType = "access"
	// TypeRefresh là token dùng cho cookie refreshToken.
	TypeRefresh TokenType = "refresh"
)

// Claims là payload JWT của Services.
type Claims struct {
	UserID uuid.UUID `json:"userId"`
	Role   string    `json:"role"`
	Type   TokenType `json:"type"`
	jwt.RegisteredClaims
}

// Manager quản lý việc ký và xác thực token theo secret/TTL cấu hình.
type Manager struct {
	secret     []byte
	accessTTL  time.Duration
	refreshTTL time.Duration
}

// NewManager tạo Manager mới từ secret và TTL (phút access, giờ refresh).
func NewManager(secret string, accessTTLMinutes, refreshTTLHours int) *Manager {
	return &Manager{
		secret:     []byte(secret),
		accessTTL:  time.Duration(accessTTLMinutes) * time.Minute,
		refreshTTL: time.Duration(refreshTTLHours) * time.Hour,
	}
}

// GenerateAccess ký access token HS256 cho user.
func (m *Manager) GenerateAccess(userID uuid.UUID, role string) (string, error) {
	return m.generate(userID, role, TypeAccess, m.accessTTL)
}

// GenerateRefresh ký refresh token HS256 cho user.
func (m *Manager) GenerateRefresh(userID uuid.UUID, role string) (string, error) {
	return m.generate(userID, role, TypeRefresh, m.refreshTTL)
}

// Parse xác thực chữ ký/hạn token và trả claim; loại token được kiểm tra ở tầng gọi.
func (m *Manager) Parse(tokenString string) (*Claims, error) {
	claims := &Claims{}
	token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (any, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("phương thức ký không hợp lệ: %v", token.Header["alg"])
		}
		return m.secret, nil
	})
	if err != nil {
		return nil, fmt.Errorf("xác thực token thất bại: %w", err)
	}
	if !token.Valid {
		return nil, fmt.Errorf("token không hợp lệ")
	}
	return claims, nil
}

// ParseAccess xác thực và đảm bảo token là access token.
func (m *Manager) ParseAccess(tokenString string) (*Claims, error) {
	claims, err := m.Parse(tokenString)
	if err != nil {
		return nil, err
	}
	if claims.Type != TypeAccess {
		return nil, fmt.Errorf("token không phải access token")
	}
	return claims, nil
}

// ParseRefresh xác thực và đảm bảo token là refresh token.
func (m *Manager) ParseRefresh(tokenString string) (*Claims, error) {
	claims, err := m.Parse(tokenString)
	if err != nil {
		return nil, err
	}
	if claims.Type != TypeRefresh {
		return nil, fmt.Errorf("token không phải refresh token")
	}
	return claims, nil
}

// RefreshTTL trả về thời hạn của refresh token (dùng để set Max-Age cookie).
func (m *Manager) RefreshTTL() time.Duration {
	return m.refreshTTL
}

// generate ký token với loại và TTL chỉ định.
func (m *Manager) generate(userID uuid.UUID, role string, tokenType TokenType, ttl time.Duration) (string, error) {
	now := time.Now().UTC()
	claims := Claims{
		UserID: userID,
		Role:   role,
		Type:   tokenType,
		RegisteredClaims: jwt.RegisteredClaims{
			Subject:   userID.String(),
			IssuedAt:  jwt.NewNumericDate(now),
			ExpiresAt: jwt.NewNumericDate(now.Add(ttl)),
		},
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	signed, err := token.SignedString(m.secret)
	if err != nil {
		return "", fmt.Errorf("ký token thất bại: %w", err)
	}
	return signed, nil
}
