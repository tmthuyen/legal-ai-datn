package service

import (
	"context"

	"github.com/google/uuid"

	"github.com/legalai/services/internal/domain"
)

// AdminService xử lý nghiệp vụ quản trị: danh sách người dùng, khoá/mở khoá, thống kê.
type AdminService struct {
	users         domain.UserRepository
	conversations domain.ConversationRepository
	messages      domain.MessageRepository
}

// NewAdminService tạo AdminService mới.
func NewAdminService(
	users domain.UserRepository,
	conversations domain.ConversationRepository,
	messages domain.MessageRepository,
) *AdminService {
	return &AdminService{users: users, conversations: conversations, messages: messages}
}

// Analytics là số liệu tổng quan trả cho dashboard admin.
type Analytics struct {
	TotalUsers         int64
	TotalConversations int64
	TotalQuestions     int64
}

// ListUsers trả danh sách người dùng phân trang, lọc theo `search` (email/username).
func (s *AdminService) ListUsers(ctx context.Context, params domain.PaginationParams, search string) ([]domain.User, *domain.Pagination, error) {
	users, total, err := s.users.List(ctx, params, search)
	if err != nil {
		return nil, nil, domain.ErrInternal("Không thể lấy danh sách người dùng", err.Error())
	}
	return users, buildPagination(total, params), nil
}

// UpdateUserStatus khoá/mở khoá tài khoản; lỗi 404 nếu không có user.
func (s *AdminService) UpdateUserStatus(ctx context.Context, userID uuid.UUID, isActive bool) (*domain.User, error) {
	user, err := s.users.FindByID(ctx, userID)
	if err != nil {
		return nil, domain.ErrInternal("Không thể xử lý yêu cầu", err.Error())
	}
	if user == nil {
		return nil, domain.ErrNotFound("Không tìm thấy người dùng")
	}

	user.IsActive = isActive
	if err := s.users.Update(ctx, user); err != nil {
		return nil, domain.ErrInternal("Không thể cập nhật người dùng", err.Error())
	}
	return user, nil
}

// Analytics thống kê tổng số người dùng, hội thoại và câu hỏi pháp luật.
func (s *AdminService) GetAnalytics(ctx context.Context) (*Analytics, error) {
	totalUsers, err := s.users.Count(ctx)
	if err != nil {
		return nil, domain.ErrInternal("Không thể thống kê người dùng", err.Error())
	}
	totalConversations, err := s.conversations.Count(ctx)
	if err != nil {
		return nil, domain.ErrInternal("Không thể thống kê hội thoại", err.Error())
	}
	totalQuestions, err := s.messages.CountBySender(ctx, domain.SenderUser)
	if err != nil {
		return nil, domain.ErrInternal("Không thể thống kê câu hỏi", err.Error())
	}

	return &Analytics{
		TotalUsers:         totalUsers,
		TotalConversations: totalConversations,
		TotalQuestions:     totalQuestions,
	}, nil
}
