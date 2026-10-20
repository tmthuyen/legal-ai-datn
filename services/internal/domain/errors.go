package domain

import "fmt"

// BusinessError là lỗi nghiệp vụ kèm statusCode HTTP tương ứng.
// Handler trả lỗi này qua response.Error để đảm bảo HTTP status == statusCode.
type BusinessError struct {
	StatusCode int
	Message    string
	Errors     []string
}

// Error cài đặt interface error.
func (e *BusinessError) Error() string {
	return fmt.Sprintf("business error %d: %s", e.StatusCode, e.Message)
}

// NewBusinessError tạo lỗi nghiệp vụ với statusCode, message và danh sách chi tiết.
func NewBusinessError(statusCode int, message string, errors ...string) *BusinessError {
	return &BusinessError{StatusCode: statusCode, Message: message, Errors: errors}
}

// ErrBadRequest tạo lỗi 400 với message và chi tiết cho trước.
func ErrBadRequest(message string, details ...string) *BusinessError {
	return NewBusinessError(400, message, details...)
}

// ErrUnauthorized tạo lỗi 401 (thiếu/sai/hết hạn token).
func ErrUnauthorized(message string, details ...string) *BusinessError {
	return NewBusinessError(401, message, details...)
}

// ErrForbidden tạo lỗi 403 (không đủ quyền).
func ErrForbidden(message string, details ...string) *BusinessError {
	return NewBusinessError(403, message, details...)
}

// ErrNotFound tạo lỗi 404 (không tìm thấy tài nguyên).
func ErrNotFound(message string, details ...string) *BusinessError {
	return NewBusinessError(404, message, details...)
}

// ErrConflict tạo lỗi 409 (trùng lặp email/username).
func ErrConflict(message string, details ...string) *BusinessError {
	return NewBusinessError(409, message, details...)
}

// ErrUnprocessable tạo lỗi 422 (body sai schema).
func ErrUnprocessable(message string, details ...string) *BusinessError {
	return NewBusinessError(422, message, details...)
}

// ErrInternal tạo lỗi 500 (lỗi hệ thống, không lộ chi tiết nội bộ).
func ErrInternal(message string, details ...string) *BusinessError {
	return NewBusinessError(500, message, details...)
}

// ErrBadGateway tạo lỗi 502 (Backend AI không phản hồi hợp lệ).
func ErrBadGateway(message string, details ...string) *BusinessError {
	return NewBusinessError(502, message, details...)
}
