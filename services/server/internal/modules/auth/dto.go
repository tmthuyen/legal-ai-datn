package auth

import "server/internal/modules/user"

// RegisterRequest là payload của POST /api/v1/auth/register.
type RegisterRequest struct {
	Email    string  `json:"email" binding:"required,email"`
	Username string  `json:"username" binding:"required,min=3,max=50"`
	Password string  `json:"password" binding:"required,min=6"`
	FullName *string `json:"fullName"`
}

// LoginRequest là payload của POST /api/v1/auth/login.
type LoginRequest struct {
	Identifier string `json:"identifier" binding:"required"`
	Password   string `json:"password" binding:"required"`
}

// Response là payload trả về khi đăng nhập/đăng ký thành công.
type Response struct {
	AccessToken string        `json:"accessToken"`
	User        user.Response `json:"user"`
}
