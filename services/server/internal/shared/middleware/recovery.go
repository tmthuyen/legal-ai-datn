package middleware

import (
	"log"
	"net/http"
	"runtime/debug"

	"github.com/gin-gonic/gin"

	"server/internal/shared/response"
)

// Recovery bắt panic xảy ra trong handler và trả về 500 an toàn.
func Recovery() gin.HandlerFunc {
	return func(c *gin.Context) {
		defer func() {
			if r := recover(); r != nil {
				log.Printf("[PANIC RECOVER] %v\nStack trace:\n%s", r, debug.Stack())
				response.Error(c, http.StatusInternalServerError, "Lỗi máy chủ nội bộ", []string{"Hệ thống gặp sự cố không mong muốn"})
				c.Abort()
			}
		}()
		c.Next()
	}
}
