// Package response cung cấp cấu trúc envelope JSON chuẩn theo API contract.
package response

import (
	"github.com/gin-gonic/gin"
)

// SuccessResponse là envelope chuẩn khi request thành công.
type SuccessResponse struct {
	Success    bool   `json:"success"`
	StatusCode int    `json:"statusCode"`
	Message    string `json:"message"`
	Data       any    `json:"data"`
}

// PaginatedResponse là envelope chuẩn cho danh sách có phân trang.
type PaginatedResponse struct {
	Success    bool       `json:"success"`
	StatusCode int        `json:"statusCode"`
	Message    string     `json:"message"`
	Data       any        `json:"data"`
	Pagination Pagination `json:"pagination"`
}

// Pagination mô tả thông tin phân trang trả về cho client.
type Pagination struct {
	Total      int64 `json:"total"`
	Page       int   `json:"page"`
	Limit      int   `json:"limit"`
	TotalPages int   `json:"totalPages"`
}

// ErrorResponse là envelope chuẩn khi xảy ra lỗi.
type ErrorResponse struct {
	Success    bool     `json:"success"`
	StatusCode int      `json:"statusCode"`
	Message    string   `json:"message"`
	Errors     []string `json:"errors"`
}

// Success ghi response thành công với HTTP status = statusCode trong body.
func Success(c *gin.Context, statusCode int, message string, data any) {
	c.JSON(statusCode, SuccessResponse{
		Success:    true,
		StatusCode: statusCode,
		Message:    message,
		Data:       data,
	})
}

// Paginated ghi response danh sách phân trang với HTTP status = statusCode trong body.
func Paginated(c *gin.Context, statusCode int, message string, data any, pagination Pagination) {
	c.JSON(statusCode, PaginatedResponse{
		Success:    true,
		StatusCode: statusCode,
		Message:    message,
		Data:       data,
		Pagination: pagination,
	})
}

// Error ghi response lỗi với HTTP status = statusCode trong body.
func Error(c *gin.Context, statusCode int, message string, errors []string) {
	if errors == nil {
		errors = []string{}
	}
	c.JSON(statusCode, ErrorResponse{
		Success:    false,
		StatusCode: statusCode,
		Message:    message,
		Errors:     errors,
	})
}
