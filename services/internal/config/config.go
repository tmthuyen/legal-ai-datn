// Package config nạp cấu hình Services từ biến môi trường (.env) vào struct Config.
package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/joho/godotenv"
)

// Config load từ .env
type Config struct {
	AppPort string
	GinMode string

	DBHost     string
	DBPort     string
	DBUser     string
	DBPassword string
	DBName     string
	DBSSLMode  string

	JWTSecret          string
	JWTAccessTTLMinute int
	JWTRefreshTTLHour  int

	CORSAllowedOrigins []string

	AIBackendURL            string
	AIBackendTimeoutSeconds int

	CookieSecure bool
}

// Load .env
func Load() (*Config, error) {
	if err := godotenv.Load(); err != nil && !os.IsNotExist(err) {
		if _, statErr := os.Stat(".env"); statErr == nil {
			return nil, fmt.Errorf("đọc file .env thất bại: %w", err)
		}
	}

	cfg := &Config{
		AppPort:                 getEnv("APP_PORT", "8080"),
		GinMode:                 getEnv("GIN_MODE", "debug"),
		DBHost:                  getEnv("DB_HOST", "localhost"),
		DBPort:                  getEnv("DB_PORT", "5432"),
		DBUser:                  getEnv("DB_USER", "legalai"),
		DBPassword:              getEnv("DB_PASSWORD", "legalai"),
		DBName:                  getEnv("DB_NAME", "legalai"),
		DBSSLMode:               getEnv("DB_SSLMODE", "disable"),
		JWTSecret:               getEnv("JWT_SECRET", ""),
		CORSAllowedOrigins:      splitAndTrim(getEnv("CORS_ALLOWED_ORIGINS", "http://localhost:3003")),
		AIBackendURL:            strings.TrimRight(getEnv("AI_BACKEND_URL", "http://localhost:8090"), "/"),
		AIBackendTimeoutSeconds: 60,
		CookieSecure:            false,
	}

	if cfg.JWTSecret == "" {
		return nil, fmt.Errorf("thiếu biến môi trường bắt buộc JWT_SECRET")
	}
	if len(cfg.JWTSecret) < 32 {
		return nil, fmt.Errorf("JWT_SECRET phải có độ dài tối thiểu 32 ký tự")
	}

	accessTTL, err := getEnvInt("JWT_ACCESS_TTL_MINUTES", 15)
	if err != nil {
		return nil, err
	}
	cfg.JWTAccessTTLMinute = accessTTL

	refreshTTL, err := getEnvInt("JWT_REFRESH_TTL_HOURS", 168)
	if err != nil {
		return nil, err
	}
	cfg.JWTRefreshTTLHour = refreshTTL

	aiTimeout, err := getEnvInt("AI_BACKEND_TIMEOUT_SECONDS", 60)
	if err != nil {
		return nil, err
	}
	cfg.AIBackendTimeoutSeconds = aiTimeout

	cookieSecure, err := getEnvBool("COOKIE_SECURE", false)
	if err != nil {
		return nil, err
	}
	cfg.CookieSecure = cookieSecure

	return cfg, nil
}

// DSN dựng chuỗi kết nối PostgreSQL cho GORM.
func (c *Config) DSN() string {
	return fmt.Sprintf(
		"host=%s port=%s user=%s password=%s dbname=%s sslmode=%s",
		c.DBHost, c.DBPort, c.DBUser, c.DBPassword, c.DBName, c.DBSSLMode,
	)
}

// getEnv trả về giá trị biến môi trường, hoặc giá trị mặc định khi rỗng.
func getEnv(key, fallback string) string {
	if value := strings.TrimSpace(os.Getenv(key)); value != "" {
		return value
	}
	return fallback
}

// getEnvInt đọc biến môi trường kiểu số nguyên, có giá trị mặc định.
func getEnvInt(key string, fallback int) (int, error) {
	raw := strings.TrimSpace(os.Getenv(key))
	if raw == "" {
		return fallback, nil
	}
	value, err := strconv.Atoi(raw)
	if err != nil {
		return 0, fmt.Errorf("biến %s phải là số nguyên: %w", key, err)
	}
	return value, nil
}

// getEnvBool đọc biến môi trường kiểu boolean, có giá trị mặc định.
func getEnvBool(key string, fallback bool) (bool, error) {
	raw := strings.TrimSpace(os.Getenv(key))
	if raw == "" {
		return fallback, nil
	}
	value, err := strconv.ParseBool(raw)
	if err != nil {
		return false, fmt.Errorf("biến %s phải là true/false: %w", key, err)
	}
	return value, nil
}

// splitAndTrim tách chuỗi theo dấu phẩy, bỏ khoảng trắng và phần tử rỗng.
func splitAndTrim(raw string) []string {
	parts := strings.Split(raw, ",")
	result := make([]string, 0, len(parts))
	for _, part := range parts {
		if trimmed := strings.TrimSpace(part); trimmed != "" {
			result = append(result, trimmed)
		}
	}
	return result
}
