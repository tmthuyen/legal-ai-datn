// Package hash cung cấp tiện ích băm và xác thực mật khẩu qua bcrypt.
package hash

import (
	"fmt"

	"golang.org/x/crypto/bcrypt"
)

// Password băm mật khẩu dạng plain text thành chuỗi bcrypt.
func Password(plain string) (string, error) {
	bytes, err := bcrypt.GenerateFromPassword([]byte(plain), bcrypt.DefaultCost)
	if err != nil {
		return "", fmt.Errorf("băm mật khẩu thất bại: %w", err)
	}
	return string(bytes), nil
}

// CheckPassword so khớp mật khẩu plain text với chuỗi hash bcrypt đã lưu.
func CheckPassword(plain, hashed string) bool {
	return bcrypt.CompareHashAndPassword([]byte(hashed), []byte(plain)) == nil
}
