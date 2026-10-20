package main

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

	"github.com/gin-gonic/gin"

	"github.com/legalai/services/internal/aiclient"
	"github.com/legalai/services/internal/config"
	"github.com/legalai/services/internal/domain"
	"github.com/legalai/services/internal/handler"
	"github.com/legalai/services/internal/middleware"
	"github.com/legalai/services/internal/repository"
	"github.com/legalai/services/internal/service"
	"github.com/legalai/services/pkg/jwt"
)

func main() {
	if err := run(); err != nil {
		log.Fatalf("Services khởi động thất bại: %v", err)
	}
}

// run nạp cấu hình, kết nối DB, wiring dependency và chạy HTTP server.
func run() error {
	cfg, err := config.Load()
	if err != nil {
		return fmt.Errorf("nạp cấu hình thất bại: %w", err)
	}

	gin.SetMode(cfg.GinMode)

	db, err := repository.NewDB(cfg.DSN(), cfg.GinMode)
	if err != nil {
		return fmt.Errorf("kết nối cơ sở dữ liệu thất bại: %w", err)
	}
	if err := repository.Migrate(db); err != nil {
		return fmt.Errorf("migrate cơ sở dữ liệu thất bại: %w", err)
	}
	if err := repository.SeedDB(db); err != nil {
		return fmt.Errorf("seed cơ sở dữ liệu thất bại: %w", err)
	}

	userRepo := repository.NewUserRepository(db)
	conversationRepo := repository.NewConversationRepository(db)
	messageRepo := repository.NewMessageRepository(db)

	jwtManager := jwt.NewManager(cfg.JWTSecret, cfg.JWTAccessTTLMinute, cfg.JWTRefreshTTLHour)
	aiClient := aiclient.NewClient(cfg.AIBackendURL, cfg.AIBackendTimeoutSeconds)

	authService := service.NewAuthService(userRepo, jwtManager)
	userService := service.NewUserService(userRepo)
	chatService := service.NewChatService(conversationRepo, messageRepo, aiClient)
	adminService := service.NewAdminService(userRepo, conversationRepo, messageRepo)

	authHandler := handler.NewAuthHandler(authService, jwtManager, cfg.CookieSecure)
	userHandler := handler.NewUserHandler(userService)
	chatHandler := handler.NewChatHandler(chatService)
	adminHandler := handler.NewAdminHandler(adminService)
	healthHandler := handler.NewHealthHandler()

	router := buildRouter(cfg, jwtManager, authHandler, userHandler, chatHandler, adminHandler, healthHandler)

	server := &http.Server{
		Addr:    ":" + cfg.AppPort,
		Handler: router,
	}

	return serve(server, cfg.AppPort)
}

// buildRouter dựng Gin engine cùng toàn bộ route theo API contract.
func buildRouter(
	cfg *config.Config,
	jwtManager *jwt.Manager,
	authHandler *handler.AuthHandler,
	userHandler *handler.UserHandler,
	chatHandler *handler.ChatHandler,
	adminHandler *handler.AdminHandler,
	healthHandler *handler.HealthHandler,
) *gin.Engine {
	router := gin.New()
	router.Use(middleware.Logger(), middleware.Recovery(), middleware.CORS(cfg.CORSAllowedOrigins))

	api := router.Group("/api/v1")

	api.GET("/health", healthHandler.Health)

	auth := api.Group("/auth")
	auth.POST("/register", authHandler.Register)
	auth.POST("/login", authHandler.Login)
	auth.POST("/refresh", authHandler.Refresh)
	auth.POST("/logout", authHandler.Logout)

	authenticated := api.Group("")
	authenticated.Use(middleware.RequireAuth(jwtManager))
	authenticated.GET("/auth/me", authHandler.Me)

	user := authenticated.Group("/user")
	user.PUT("/profile", userHandler.UpdateProfile)
	user.PUT("/password", userHandler.ChangePassword)

	chat := authenticated.Group("/chat")
	chat.GET("/conversations", chatHandler.ListConversations)
	chat.POST("/conversations", chatHandler.CreateConversation)
	chat.DELETE("/conversations/:id", chatHandler.DeleteConversation)
	chat.GET("/conversations/:id/messages", chatHandler.ListMessages)
	chat.POST("/conversations/:id/messages", chatHandler.SendMessage)

	admin := authenticated.Group("/admin")
	admin.Use(middleware.RequireRole(domain.RoleAdmin))
	admin.GET("/users", adminHandler.ListUsers)
	admin.PUT("/users/:id/status", adminHandler.UpdateUserStatus)
	admin.GET("/analytics", adminHandler.Analytics)

	return router
}

// serve chạy HTTP server và shutdown graceful khi nhận tín hiệu kết thúc.
func serve(server *http.Server, port string) error {
	go func() {
		log.Printf("Services đang chạy tại cổng %s", port)
		if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Printf("HTTP server dừng bất thường: %v", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := server.Shutdown(ctx); err != nil {
		return fmt.Errorf("shutdown HTTP server thất bại: %w", err)
	}
	return nil
}
