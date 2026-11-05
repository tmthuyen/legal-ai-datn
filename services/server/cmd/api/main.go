package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"

	"server/internal/infra/aiclient"
	"server/internal/infra/config"
	"server/internal/infra/database"
	"server/internal/infra/httpserver"
	"server/internal/modules/admin"
	"server/internal/modules/auth"
	"server/internal/modules/chat"
	"server/internal/modules/user"
	"server/internal/shared/jwt"
	"server/internal/shared/middleware"
	"server/internal/shared/response"
)

func main() {
	if err := run(); err != nil {
		log.Fatalf("[FATAL] Khởi động Services thất bại: %v", err)
	}
}

func run() error {
	cfg, err := config.Load()
	if err != nil {
		return fmt.Errorf("nạp cấu hình thất bại: %w", err)
	}

	gin.SetMode(cfg.GinMode)

	db, err := database.NewDB(cfg.DSN(), cfg.GinMode)
	if err != nil {
		return fmt.Errorf("kết nối cơ sở dữ liệu thất bại: %w", err)
	}

	if err := database.AutoMigrate(db, &user.User{}, &chat.Conversation{}, &chat.Message{}); err != nil {
		return fmt.Errorf("migrate thất bại: %w", err)
	}
	if err := database.SeedData(db); err != nil {
		return fmt.Errorf("seed dữ liệu thất bại: %w", err)
	}

	jwtManager := jwt.NewManager(cfg.JWTSecret, cfg.JWTAccessTTLMinute, cfg.JWTRefreshTTLHour)
	aiClient := aiclient.NewClient(cfg.AIBackendURL, cfg.AIBackendTimeoutSeconds)

	userRepo := user.NewRepository(db)
	convRepo := chat.NewConversationRepository(db)
	msgRepo := chat.NewMessageRepository(db)

	userService := user.NewService(userRepo)
	authService := auth.NewService(userRepo, jwtManager)
	chatService := chat.NewService(convRepo, msgRepo, aiClient)
	adminService := admin.NewService(userRepo, convRepo, msgRepo)

	userHandler := user.NewHandler(userService)
	authHandler := auth.NewHandler(authService, jwtManager, cfg.CookieSecure)
	chatHandler := chat.NewHandler(chatService)
	adminHandler := admin.NewHandler(adminService)

	router := gin.New()
	router.Use(middleware.Logger(), middleware.Recovery(), middleware.CORS(cfg.CORSAllowedOrigins))

	api := router.Group("/api/v1")
	api.GET("/health", func(c *gin.Context) {
		response.Success(c, http.StatusOK, "Dịch vụ hoạt động bình thường", gin.H{
			"status": "healthy",
			"time":   "ok",
		})
	})

	authMiddleware := middleware.RequireAuth(jwtManager)

	auth.RegisterRoutes(api, authHandler, authMiddleware)
	user.RegisterRoutes(api, userHandler, authMiddleware)
	chat.RegisterRoutes(api, chatHandler, authMiddleware)
	admin.RegisterRoutes(api, adminHandler, authMiddleware)

	server := &http.Server{
		Addr:    ":" + cfg.AppPort,
		Handler: router,
	}

	return httpserver.Serve(server, cfg.AppPort)
}
