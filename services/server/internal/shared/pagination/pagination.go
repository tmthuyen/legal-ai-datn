// Package pagination định nghĩa tham số và metadata phân trang.
package pagination

import (
	"strconv"

	"github.com/gin-gonic/gin"
)

// Params chứa tham số phân trang chuẩn từ query string.
type Params struct {
	Page  int
	Limit int
}

// Offset tính toán vị trí bản ghi bắt đầu cho database query.
func (p Params) Offset() int {
	return (p.Page - 1) * p.Limit
}

// Parse trích xuất page và limit từ Gin context (mặc định page=1, limit=20, max limit=100).
func Parse(c *gin.Context) Params {
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	if page < 1 {
		page = 1
	}

	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "20"))
	if limit < 1 {
		limit = 20
	}
	if limit > 100 {
		limit = 100
	}

	return Params{
		Page:  page,
		Limit: limit,
	}
}

// Meta tính toán tổng số trang và thông tin phân trang cho response.
func Meta(total int64, params Params) (int64, int, int, int) {
	totalPages := 0
	if params.Limit > 0 {
		totalPages = int((total + int64(params.Limit) - 1) / int64(params.Limit))
	}
	return total, params.Page, params.Limit, totalPages
}
