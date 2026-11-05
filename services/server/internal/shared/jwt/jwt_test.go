package jwt

import (
	"testing"

	"github.com/google/uuid"
)

func TestGenerateAndVerifyToken(t *testing.T) {
	mgr := NewManager("test-super-secret-key-1234567890", 15, 24)
	userID := uuid.New()

	access, err := mgr.GenerateAccessToken(userID, "admin")
	if err != nil {
		t.Fatalf("sinh access token thất bại: %v", err)
	}

	claims, err := mgr.VerifyToken(access, TypeAccess)
	if err != nil {
		t.Fatalf("verify access token thất bại: %v", err)
	}
	if claims.UserID != userID || claims.Role != "admin" {
		t.Errorf("claims không khớp: %+v", claims)
	}

	refresh, err := mgr.GenerateRefreshToken(userID)
	if err != nil {
		t.Fatalf("sinh refresh token thất bại: %v", err)
	}

	refreshClaims, err := mgr.VerifyToken(refresh, TypeRefresh)
	if err != nil {
		t.Fatalf("verify refresh token thất bại: %v", err)
	}
	if refreshClaims.UserID != userID {
		t.Errorf("claims refresh không khớp: %+v", refreshClaims)
	}

	// Kiểm tra sai loại token
	if _, err := mgr.VerifyToken(access, TypeRefresh); err == nil {
		t.Errorf("VerifyToken phải báo lỗi khi loại token không khớp")
	}
}
