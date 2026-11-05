package hash

import (
	"testing"
)

func TestPasswordAndCheck(t *testing.T) {
	plain := "TestPassword@123"

	hashed, err := Password(plain)
	if err != nil {
		t.Fatalf("băm mật khẩu thất bại: %v", err)
	}

	if !CheckPassword(plain, hashed) {
		t.Errorf("CheckPassword không khớp với mật khẩu gốc")
	}

	if CheckPassword("WrongPassword", hashed) {
		t.Errorf("CheckPassword chấp nhận mật khẩu sai")
	}
}
