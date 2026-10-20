// Package aiclient cung cấp HTTP client gọi Backend FastAPI (POST /api/retrieval).
package aiclient

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// RetrievalResult là payload `result` trả về từ Backend (6 key theo contract).
// Dùng con trỏ/`any` để giữ nguyên cấu trúc JSON mà Backend trả về.
type RetrievalResult struct {
	Input              string         `json:"input"`
	ExtractedHierarchy map[string]any `json:"extracted_hierarchy"`
	NodeInformation    map[string]any `json:"node_information"`
	RelatedDocuments   []any          `json:"related_documents"`
	RelatedNodes       []any          `json:"related_nodes"`
	Relationships      []any          `json:"relationships"`
}

// retrievalRequest là body gửi sang Backend.
type retrievalRequest struct {
	QueryText string `json:"query_text"`
}

// retrievalEnvelope là envelope Backend trả về (status_code snake_case).
type retrievalEnvelope struct {
	Success    bool            `json:"success"`
	StatusCode int             `json:"status_code"`
	Message    string          `json:"message"`
	Result     json.RawMessage `json:"result"`
	Errors     []string        `json:"errors"`
}

// Client là HTTP client gọi Backend FastAPI.
type Client struct {
	baseURL    string
	httpClient *http.Client
}

// NewClient tạo client mới với base URL và timeout (giây) cho trước.
func NewClient(baseURL string, timeoutSeconds int) *Client {
	return &Client{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: time.Duration(timeoutSeconds) * time.Second,
		},
	}
}

// Retrieve gọi Backend POST /api/retrieval với câu hỏi, trả RetrievalResult.
// Trả lỗi nếu mạng lỗi, timeout, HTTP không phải 2xx hoặc envelope success=false.
func (c *Client) Retrieve(ctx context.Context, query string) (*RetrievalResult, error) {
	payload, err := json.Marshal(retrievalRequest{QueryText: query})
	if err != nil {
		return nil, fmt.Errorf("mã hoá request retrieval thất bại: %w", err)
	}

	url := c.baseURL + "/api/retrieval"
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(payload))
	if err != nil {
		return nil, fmt.Errorf("tạo request retrieval thất bại: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("gọi Backend retrieval thất bại: %w", err)
	}
	defer func() {
		_ = resp.Body.Close()
	}()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("đọc response retrieval thất bại: %w", err)
	}

	var envelope retrievalEnvelope
	if err := json.Unmarshal(body, &envelope); err != nil {
		return nil, fmt.Errorf("giải mã envelope retrieval thất bại: %w", err)
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 || !envelope.Success {
		message := envelope.Message
		if message == "" {
			message = http.StatusText(resp.StatusCode)
		}
		return nil, fmt.Errorf("Backend retrieval trả lỗi (HTTP %d): %s", resp.StatusCode, message)
	}

	result := &RetrievalResult{}
	if len(envelope.Result) > 0 && string(envelope.Result) != "null" {
		if err := json.Unmarshal(envelope.Result, result); err != nil {
			return nil, fmt.Errorf("giải mã payload result thất bại: %w", err)
		}
	}
	return result, nil
}
