// Package httpserver quản lý khởi chạy HTTP Server và Graceful Shutdown an toàn.
package httpserver

import (
	"context"
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

// Serve khởi động HTTP server và chờ nhận tín hiệu SIGINT/SIGTERM để shutdown an toàn.
func Serve(server *http.Server, port string) error {
	go func() {
		log.Printf("[Server] Legal AI Services đang chạy tại cổng :%s", port)
		if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Printf("[Server] HTTP server dừng bất thường: %v", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("[Server] Đang tiến hành Graceful Shutdown...")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		return fmt.Errorf("shutdown HTTP server thất bại: %w", err)
	}
	log.Println("[Server] Server đã dừng an toàn.")
	return nil
}
