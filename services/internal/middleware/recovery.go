package middleware

import (
	"fmt"
	"log"
	"os"

	"github.com/gin-gonic/gin"

	"github.com/legalai/services/pkg/response"
)

// Recovery trả middleware bắt panic, ghi log và trả envelope 500 (không lộ chi tiết nội bộ).
func Recovery() gin.HandlerFunc {
	return func(c *gin.Context) {
		defer func() {
			if recovered := recover(); recovered != nil {
				log.Printf("[panic] %s %s: %v", c.Request.Method, c.Request.URL.Path, recovered)
				response.Error(c, 500, "Lỗi hệ thống", nil)
				c.Abort()
			}
		}()
		c.Next()
	}
}

// Logger trả middleware ghi log mỗi request ra stdout của tiến trình.
func Logger() gin.HandlerFunc {
	logger := log.New(os.Stdout, "", log.LstdFlags)
	return func(c *gin.Context) {
		c.Next()
		if len(c.Errors) > 0 {
			logger.Printf("%s %s %d - %s", c.Request.Method, c.Request.URL.Path, c.Writer.Status(), c.Errors.String())
			return
		}
		logger.Printf("%s %s %d", c.Request.Method, c.Request.URL.Path, c.Writer.Status())
	}
}

// ErrorHandler trả middleware cuối chuỗi ghi lỗi chưa xử lý thành envelope 500 nếu chưa ghi body.
func ErrorHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Next()
		if len(c.Errors) == 0 {
			return
		}
		if c.Writer.Written() {
			return
		}
		lastErr := c.Errors.Last().Err
		response.Error(c, 500, fmt.Sprintf("Lỗi hệ thống: %s", lastErr.Error()), nil)
	}
}
