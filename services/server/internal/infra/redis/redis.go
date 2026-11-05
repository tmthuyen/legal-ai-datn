// Package redis cung cấp wrapper cho Redis client (hỗ trợ Cache, Rate Limiter).
package redis

import (
	"context"
	"log"
	"time"
)

// Client đại diện cho Redis client (sẵn sàng tích hợp go-redis hoặc memory mock).
type Client struct {
	addr string
}

// NewClient khởi tạo Redis client wrapper.
func NewClient(host, port, password string) *Client {
	addr := host + ":" + port
	log.Printf("[Redis] Đã khởi tạo Redis adapter tại %s", addr)
	return &Client{addr: addr}
}

// Get lấy dữ liệu cache theo key (placeholder mở rộng).
func (c *Client) Get(ctx context.Context, key string) (string, error) {
	return "", nil
}

// Set lưu dữ liệu cache theo key với thời hạn TTL (placeholder mở rộng).
func (c *Client) Set(ctx context.Context, key string, value any, ttl time.Duration) error {
	return nil
}

// Del xoá key khỏi cache.
func (c *Client) Del(ctx context.Context, key string) error {
	return nil
}
