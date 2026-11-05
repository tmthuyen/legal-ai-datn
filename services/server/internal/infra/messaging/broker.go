// Package messaging cung cấp abstraction cho Event Broker (Producer / Consumer).
package messaging

import (
	"context"
	"log"
)

// EventBroker định nghĩa giao tiếp gửi/nhận sự kiện nền.
type EventBroker interface {
	Publish(ctx context.Context, topic string, payload any) error
	Subscribe(ctx context.Context, topic string, handler func(payload []byte) error) error
}

// MemoryBroker là implementation broker cục bộ trong bộ nhớ (mẫu mở rộng).
type MemoryBroker struct{}

// NewMemoryBroker tạo broker sự kiện nền.
func NewMemoryBroker() *MemoryBroker {
	return &MemoryBroker{}
}

// Publish gửi sự kiện vào topic.
func (b *MemoryBroker) Publish(ctx context.Context, topic string, payload any) error {
	log.Printf("[Messaging] Published event to topic %s", topic)
	return nil
}

// Subscribe lắng nghe sự kiện từ topic.
func (b *MemoryBroker) Subscribe(ctx context.Context, topic string, handler func(payload []byte) error) error {
	return nil
}
