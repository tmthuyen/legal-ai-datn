// Package handler chứa các Gin handler mỏng, chỉ chuyển tiếp nghiệp vụ cho tầng service.
package handler

import (
	"strconv"

	"github.com/gin-gonic/gin"

	"github.com/legalai/services/internal/domain"
	"github.com/legalai/services/pkg/response"
)

// defaultPage là trang mặc định khi client không truyền.
const defaultPage = 1

// defaultLimit là số bản ghi mặc định mỗi trang.
const defaultLimit = 20

// maxLimit là số bản ghi tối đa mỗi trang theo contract.
const maxLimit = 100

// parsePagination đọc query `page`/`limit` và chuẩn hoá theo contract (page>=1, 1<=limit<=100).
func parsePagination(c *gin.Context) domain.PaginationParams {
	page := parseIntQuery(c, "page", defaultPage)
	if page < 1 {
		page = defaultPage
	}

	limit := parseIntQuery(c, "limit", defaultLimit)
	if limit < 1 {
		limit = defaultLimit
	}
	if limit > maxLimit {
		limit = maxLimit
	}

	return domain.PaginationParams{Page: page, Limit: limit}
}

// parseIntQuery đọc một query param kiểu số nguyên, trả fallback nếu thiếu hoặc không hợp lệ.
func parseIntQuery(c *gin.Context, key string, fallback int) int {
	raw := c.Query(key)
	if raw == "" {
		return fallback
	}
	value, err := strconv.Atoi(raw)
	if err != nil {
		return fallback
	}
	return value
}

// respondBusinessError trả lỗi nghiệp vụ qua envelope, giữ HTTP status bằng statusCode.
// Lỗi không phải BusinessError được coi là 500 và không lộ chi tiết nội bộ.
func respondBusinessError(c *gin.Context, err error) {
	if businessErr, ok := err.(*domain.BusinessError); ok {
		response.Error(c, businessErr.StatusCode, businessErr.Message, businessErr.Errors)
		return
	}
	response.Error(c, 500, "Lỗi hệ thống", nil)
}

// toPageMeta chuyển thông tin phân trang của domain sang payload envelope.
func toPageMeta(pagination *domain.Pagination) response.PageMeta {
	return response.PageMeta{
		Total:      pagination.Total,
		Page:       pagination.Page,
		Limit:      pagination.Limit,
		TotalPages: pagination.TotalPages,
	}
}
