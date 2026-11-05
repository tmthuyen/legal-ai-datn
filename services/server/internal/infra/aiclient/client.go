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

// RetrievalResult là payload result trả về từ Backend AI.
type RetrievalResult struct {
	Input              string         `json:"input"`
	ExtractedHierarchy map[string]any `json:"extracted_hierarchy"`
	NodeInformation    map[string]any `json:"node_information"`
	RelatedDocuments   []any          `json:"related_documents"`
	RelatedNodes       []any          `json:"related_nodes"`
	Relationships      []any          `json:"relationships"`
}

type retrievalRequest struct {
	QueryText string `json:"query_text"`
}

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

// NewClient tạo client mới với base URL và timeout cho trước.
func NewClient(baseURL string, timeoutSeconds int) *Client {
	return &Client{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: time.Duration(timeoutSeconds) * time.Second,
		},
	}
}

// Retrieve gửi câu hỏi pháp lý sang Backend FastAPI và trả về kết quả cấu trúc.
func (c *Client) Retrieve(ctx context.Context, queryText string) (*RetrievalResult, error) {
	url := fmt.Sprintf("%s/api/retrieval", c.baseURL)

	payload := retrievalRequest{QueryText: queryText}
	bodyBytes, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("serialize request body thất bại: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(bodyBytes))
	if err != nil {
		return nil, fmt.Errorf("tạo HTTP request thất bại: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("gọi Backend AI thất bại: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("đọc response body thất bại: %w", err)
	}

	var env retrievalEnvelope
	if err := json.Unmarshal(respBody, &env); err != nil {
		return nil, fmt.Errorf("parse response JSON thất bại: %w (raw: %s)", err, string(respBody))
	}

	if !env.Success || resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("backend AI trả lỗi (status %d): %s", env.StatusCode, env.Message)
	}

	var result RetrievalResult
	if err := json.Unmarshal(env.Result, &result); err != nil {
		return nil, fmt.Errorf("parse field 'result' thất bại: %w", err)
	}

	return &result, nil
}
