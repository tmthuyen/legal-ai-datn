// Package hash cung cấp hàm băm và kiểm tra mật khẩu bằng bcrypt.
package hash

import (
	"fmt"

	"golang.org/x/crypto/bcrypt"
)

// Password băm mật khẩu bằng bcrypt với cost mặc định.
func Password(plain string) (string, error) {
	hashed, err := bcrypt.GenerateFromPassword([]byte(plain), bcrypt.DefaultCost)
	if err != nil {
		return "", fmt.Errorf("băm mật khẩu thất bại: %w", err)
	}
	return string(hashed), nil
}

// Verify kiểm tra mật khẩu thô khớp với hash đã lưu.
func Verify(hashed, plain string) error {
	if err := bcrypt.CompareHashAndPassword([]byte(hashed), []byte(plain)); err != nil {
		return fmt.Errorf("mật khẩu không khớp: %w", err)
	}
	return nil
}
