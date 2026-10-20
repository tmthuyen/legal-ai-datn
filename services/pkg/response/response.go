// Package response cung cấp helper dựng envelope chuẩn cho mọi endpoint Services.
// Mọi handler bắt buộc trả response qua package này; cấm tự gọi c.JSON.
package response

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// Envelope là cấu trúc response thành công (thành công có thể có hoặc không có phân trang).
type Envelope struct {
	Success    bool      `json:"success"`
	StatusCode int       `json:"statusCode"`
	Message    string    `json:"message"`
	Result     any       `json:"result"`
	Pagination *PageMeta `json:"pagination,omitempty"`
}

// PageMeta mô tả thông tin phân trang trong envelope.
type PageMeta struct {
	Total      int64 `json:"total"`
	Page       int   `json:"page"`
	Limit      int   `json:"limit"`
	TotalPages int   `json:"totalPages"`
}

// ErrorEnvelope là cấu trúc response lỗi.
type ErrorEnvelope struct {
	Success    bool     `json:"success"`
	StatusCode int      `json:"statusCode"`
	Message    string   `json:"message"`
	Errors     []string `json:"errors"`
}

// Success ghi envelope thành công với statusCode bằng HTTP status.
func Success(c *gin.Context, statusCode int, message string, data any) {
	c.JSON(statusCode, Envelope{
		Success:    true,
		StatusCode: statusCode,
		Message:    message,
		Result:     data,
	})
}

// Paginated ghi envelope thành công kèm thông tin phân trang.
func Paginated(c *gin.Context, statusCode int, message string, data any, meta PageMeta) {
	c.JSON(statusCode, Envelope{
		Success:    true,
		StatusCode: statusCode,
		Message:    message,
		Result:     data,
		Pagination: &meta,
	})
}

// Error ghi envelope lỗi với statusCode bằng HTTP status.
// Danh sách errors luôn là mảng (không null) để Frontend xử lý thống nhất.
func Error(c *gin.Context, statusCode int, message string, errors []string) {
	if errors == nil {
		errors = []string{}
	}
	c.JSON(statusCode, ErrorEnvelope{
		Success:    false,
		StatusCode: statusCode,
		Message:    message,
		Errors:     errors,
	})
}

// MessageOK trả envelope thành công chuẩn cho các thao tác không có dữ liệu (result = null).
func MessageOK(c *gin.Context, message string) {
	Success(c, http.StatusOK, message, nil)
}
