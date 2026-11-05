// Package apperror định nghĩa lỗi nghiệp vụ và mã HTTP tương ứng.
package apperror

import (
	"errors"
	"fmt"
	"net/http"
)

// BusinessError đại diện cho lỗi nghiệp vụ mang mã HTTP và chi tiết lỗi.
type BusinessError struct {
	StatusCode int
	Message    string
	Detail     string
}

// Error trả về thông điệp lỗi biểu diễn bằng chuỗi.
func (e *BusinessError) Error() string {
	if e.Detail != "" {
		return fmt.Sprintf("%s: %s", e.Message, e.Detail)
	}
	return e.Message
}

// ErrNotFound tạo lỗi 404 Not Found.
func ErrNotFound(message string) *BusinessError {
	return &BusinessError{StatusCode: http.StatusNotFound, Message: message}
}

// ErrBadRequest tạo lỗi 400 Bad Request.
func ErrBadRequest(message string) *BusinessError {
	return &BusinessError{StatusCode: http.StatusBadRequest, Message: message}
}

// ErrUnauthorized tạo lỗi 401 Unauthorized.
func ErrUnauthorized(message string) *BusinessError {
	return &BusinessError{StatusCode: http.StatusUnauthorized, Message: message}
}

// ErrForbidden tạo lỗi 403 Forbidden.
func ErrForbidden(message string) *BusinessError {
	return &BusinessError{StatusCode: http.StatusForbidden, Message: message}
}

// ErrConflict tạo lỗi 409 Conflict.
func ErrConflict(message string) *BusinessError {
	return &BusinessError{StatusCode: http.StatusConflict, Message: message}
}

// ErrUnprocessable tạo lỗi 422 Unprocessable Entity.
func ErrUnprocessable(message string, detail string) *BusinessError {
	return &BusinessError{StatusCode: http.StatusUnprocessableEntity, Message: message, Detail: detail}
}

// ErrInternal tạo lỗi 500 Internal Server Error.
func ErrInternal(message string, detail string) *BusinessError {
	return &BusinessError{StatusCode: http.StatusInternalServerError, Message: message, Detail: detail}
}

// ErrBadGateway tạo lỗi 502 Bad Gateway khi dịch vụ ngoài thất bại.
func ErrBadGateway(message string, detail string) *BusinessError {
	return &BusinessError{StatusCode: http.StatusBadGateway, Message: message, Detail: detail}
}

// AsBusinessError chuyển error sang BusinessError nếu có thể.
func AsBusinessError(err error) (*BusinessError, bool) {
	var bErr *BusinessError
	if errors.As(err, &bErr) {
		return bErr, true
	}
	return nil, false
}
