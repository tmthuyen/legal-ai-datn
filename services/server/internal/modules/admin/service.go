package admin

import (
	"context"
	"fmt"

	"github.com/google/uuid"

	"server/internal/modules/chat"
	"server/internal/modules/user"
	"server/internal/shared/apperror"
	"server/internal/shared/pagination"
)

// Service xử lý nghiệp vụ quản trị viên và analytics.
type Service struct {
	users         user.Repository
	conversations chat.ConversationRepository
	messages      chat.MessageRepository
}

// NewService tạo Admin Service mới.
func NewService(
	users user.Repository,
	conversations chat.ConversationRepository,
	messages chat.MessageRepository,
) *Service {
	return &Service{
		users:         users,
		conversations: conversations,
		messages:      messages,
	}
}

// ListUsers lấy danh sách người dùng phân trang và lọc theo search.
func (s *Service) ListUsers(ctx context.Context, params pagination.Params, search string) ([]user.User, int64, error) {
	users, total, err := s.users.List(ctx, params, search)
	if err != nil {
		return nil, 0, apperror.ErrInternal("Lấy danh sách người dùng thất bại", err.Error())
	}
	return users, total, nil
}

// UpdateUserStatus cập nhật trạng thái isActive của user.
func (s *Service) UpdateUserStatus(ctx context.Context, targetUserID uuid.UUID, isActive bool) (*user.User, error) {
	u, err := s.users.FindByID(ctx, targetUserID)
	if err != nil {
		return nil, apperror.ErrInternal("Tìm người dùng thất bại", err.Error())
	}
	if u == nil {
		return nil, apperror.ErrNotFound("Không tìm thấy người dùng")
	}

	u.IsActive = isActive
	if err := s.users.Update(ctx, u); err != nil {
		return nil, apperror.ErrInternal("Cập nhật trạng thái thất bại", err.Error())
	}
	return u, nil
}

// GetAnalytics thống kê số liệu tổng quan của hệ thống.
func (s *Service) GetAnalytics(ctx context.Context) (*AnalyticsResponse, error) {
	totalUsers, err := s.users.Count(ctx)
	if err != nil {
		return nil, fmt.Errorf("đếm users thất bại: %w", err)
	}

	totalConversations, err := s.conversations.Count(ctx)
	if err != nil {
		return nil, fmt.Errorf("đếm conversations thất bại: %w", err)
	}

	userMsgs, err := s.messages.CountBySender(ctx, chat.SenderUser)
	if err != nil {
		return nil, fmt.Errorf("đếm tin nhắn user thất bại: %w", err)
	}

	botMsgs, err := s.messages.CountBySender(ctx, chat.SenderBot)
	if err != nil {
		return nil, fmt.Errorf("đếm tin nhắn bot thất bại: %w", err)
	}

	return &AnalyticsResponse{
		TotalUsers:         totalUsers,
		TotalConversations: totalConversations,
		TotalMessages:      userMsgs + botMsgs,
		UserMessages:       userMsgs,
		BotMessages:        botMsgs,
	}, nil
}
