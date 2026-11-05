package admin

// UpdateUserStatusRequest là payload cập nhật trạng thái hoạt động của user.
type UpdateUserStatusRequest struct {
	IsActive bool `json:"isActive"`
}

// AnalyticsResponse là thống kê tổng quan hệ thống.
type AnalyticsResponse struct {
	TotalUsers         int64 `json:"totalUsers"`
	TotalConversations int64 `json:"totalConversations"`
	TotalMessages      int64 `json:"totalMessages"`
	UserMessages       int64 `json:"userMessages"`
	BotMessages        int64 `json:"botMessages"`
}
