package user

import "time"

// UpdateProfileRequest là payload của PUT /api/v1/user/profile.
type UpdateProfileRequest struct {
	FullName  *string `json:"fullName"`
	AvatarURL *string `json:"avatarUrl"`
}

// ChangePasswordRequest là payload của PUT /api/v1/user/password.
type ChangePasswordRequest struct {
	OldPassword string `json:"oldPassword" binding:"required"`
	NewPassword string `json:"newPassword" binding:"required,min=6"`
}

// Response là DTO trả về thông tin người dùng an toàn (không lộ passwordHash).
type Response struct {
	ID        string  `json:"id"`
	Email     string  `json:"email"`
	Username  string  `json:"username"`
	FullName  *string `json:"fullName"`
	AvatarURL *string `json:"avatarUrl"`
	Role      string  `json:"role"`
	IsActive  bool    `json:"isActive"`
	CreatedAt string  `json:"createdAt"`
	UpdatedAt string  `json:"updatedAt"`
}

// ToResponse chuyển User entity sang DTO Response.
func ToResponse(u *User) Response {
	if u == nil {
		return Response{}
	}
	return Response{
		ID:        u.ID.String(),
		Email:     u.Email,
		Username:  u.Username,
		FullName:  u.FullName,
		AvatarURL: u.AvatarURL,
		Role:      string(u.Role),
		IsActive:  u.IsActive,
		CreatedAt: u.CreatedAt.Format(time.RFC3339),
		UpdatedAt: u.UpdatedAt.Format(time.RFC3339),
	}
}

// ToResponseList chuyển danh sách User entity sang danh sách Response DTO.
func ToResponseList(users []User) []Response {
	res := make([]Response, len(users))
	for i := range users {
		res[i] = ToResponse(&users[i])
	}
	return res
}
