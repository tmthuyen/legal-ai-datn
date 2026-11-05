// Package config định nghĩa cấu hình hệ thống nạp từ biến môi trường (.env).
package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/joho/godotenv"
)

// Config chứa toàn bộ tham số cấu hình của ứng dụng.
type Config struct {
	AppPort                 string
	GinMode                 string
	DBHost                  string
	DBPort                  string
	DBUser                  string
	DBPassword              string
	DBName                  string
	DBSSLMode               string
	JWTSecret               string
	JWTAccessTTLMinute      int
	JWTRefreshTTLHour       int
	CookieSecure            bool
	CORSAllowedOrigins      []string
	AIBackendURL            string
	AIBackendTimeoutSeconds int
	RedisHost               string
	RedisPort               string
	RedisPassword           string
}

// Load đọc biến môi trường từ .env (nếu có) và trả về struct Config.
func Load() (*Config, error) {
	_ = godotenv.Load()

	cfg := &Config{
		AppPort:                 getEnv("APP_PORT", "8080"),
		GinMode:                 getEnv("GIN_MODE", "debug"),
		DBHost:                  getEnv("DB_HOST", "localhost"),
		DBPort:                  getEnv("DB_PORT", "5432"),
		DBUser:                  getEnv("DB_USER", "postgres"),
		DBPassword:              getEnv("DB_PASSWORD", "postgres"),
		DBName:                  getEnv("DB_NAME", "legal_ai_db"),
		DBSSLMode:               getEnv("DB_SSLMODE", "disable"),
		JWTSecret:               getEnv("JWT_SECRET", "super-secret-jwt-key-change-in-production"),
		JWTAccessTTLMinute:      getEnvAsInt("JWT_ACCESS_TTL_MINUTE", 15),
		JWTRefreshTTLHour:       getEnvAsInt("JWT_REFRESH_TTL_HOUR", 168),
		CookieSecure:            getEnvAsBool("COOKIE_SECURE", false),
		CORSAllowedOrigins:      parseList(getEnv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3003")),
		AIBackendURL:            getEnv("AI_BACKEND_URL", "http://localhost:8000"),
		AIBackendTimeoutSeconds: getEnvAsInt("AI_BACKEND_TIMEOUT_SECONDS", 60),
		RedisHost:               getEnv("REDIS_HOST", "localhost"),
		RedisPort:               getEnv("REDIS_PORT", "6379"),
		RedisPassword:           getEnv("REDIS_PASSWORD", ""),
	}

	if cfg.JWTSecret == "" {
		return nil, fmt.Errorf("JWT_SECRET không được để trống")
	}

	return cfg, nil
}

// DSN tạo connection string kết nối PostgreSQL.
func (c *Config) DSN() string {
	return fmt.Sprintf(
		"host=%s port=%s user=%s password=%s dbname=%s sslmode=%s TimeZone=Asia/Ho_Chi_Minh",
		c.DBHost, c.DBPort, c.DBUser, c.DBPassword, c.DBName, c.DBSSLMode,
	)
}

func getEnv(key, defaultVal string) string {
	if val, ok := os.LookupEnv(key); ok && val != "" {
		return val
	}
	return defaultVal
}

func getEnvAsInt(key string, defaultVal int) int {
	valStr := getEnv(key, "")
	if val, err := strconv.Atoi(valStr); err == nil {
		return val
	}
	return defaultVal
}

func getEnvAsBool(key string, defaultVal bool) bool {
	valStr := getEnv(key, "")
	if val, err := strconv.ParseBool(valStr); err == nil {
		return val
	}
	return defaultVal
}

func parseList(val string) []string {
	if val == "" {
		return []string{}
	}
	items := strings.Split(val, ",")
	res := make([]string, 0, len(items))
	for _, item := range items {
		trimmed := strings.TrimSpace(item)
		if trimmed != "" {
			res = append(res, trimmed)
		}
	}
	return res
}
