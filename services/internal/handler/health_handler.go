package handler

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"

	"github.com/legalai/services/pkg/response"
)

// HealthHandler xử lý endpoint kiểm tra trạng thái dịch vụ.
type HealthHandler struct{}

// NewHealthHandler tạo HealthHandler mới.
func NewHealthHandler() *HealthHandler {
	return &HealthHandler{}
}

// healthResponse là payload trạng thái dịch vụ.
type healthResponse struct {
	Status    string `json:"status"`
	Timestamp string `json:"timestamp"`
}

// Health xử lý GET /api/v1/health — 200 (không cần auth).
func (h *HealthHandler) Health(c *gin.Context) {
	response.Success(c, http.StatusOK, "OK", healthResponse{
		Status:    "ok",
		Timestamp: time.Now().UTC().Format(time.RFC3339),
	})
}
