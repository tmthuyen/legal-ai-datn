package jwt

import (
	"testing"

	"github.com/google/uuid"
)

var secret = "test-jwt-secret"
var pkg = "[JWT]"

// [Test JWT] Func: Generate & Verify Access Token
func TestGenerateVerifyAccessToken(t *testing.T) {
	// manager
	m := NewManager(secret, 10, 24)

	uId := uuid.New()
	role := "user"

	token, err := m.GenerateAccess(uId, role)

	if err != nil {
		t.Errorf("%s Tạo access token thất bại: %v", pkg, err)
	}

	claims, err := m.ParseAccess(token)

	if err != nil {
		t.Errorf("%s Xác thực access token thất bại: %v", pkg, err)
	}

	// check claim
	if claims.UserID != uId || claims.Role != role || claims.Type != TypeAccess {
		t.Errorf("%s Claims token xác thực không hợp lệ", pkg)
	}

	t.Logf("%s Test Generate & Verify Access Token thành công", pkg)

}

// [Test JWT] Func: Generate & Verify Refresh Token
func TestGenerateVerifyRefreshToken(t *testing.T) {
	// manager
	m := NewManager(secret, 10, 24)

	uId := uuid.New()
	role := "user"

	token, err := m.GenerateRefresh(uId, role)

	if err != nil {
		t.Errorf("%s Tạo refresh token thất bại: %v", pkg, err)
	}

	claims, err := m.ParseRefresh(token)

	if err != nil {
		t.Errorf("%s Xác thực refresh token thất bại: %v", pkg, err)
	}

	// check claim
	if claims.UserID != uId || claims.Role != role || claims.Type != TypeRefresh {
		t.Errorf("%s Claims token xác thực không hợp lệ", pkg)
	}

	t.Logf("%s Test Generate & Verify Refresh Token thành công", pkg)
}
