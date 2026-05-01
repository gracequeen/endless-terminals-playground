FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    iproute2 \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz && \
    rm go1.21.5.linux-amd64.tar.gz

ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/home/user/go"
ENV GOCACHE="/home/user/.cache/go-build"

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/profilesvc/internal/cache && \
    mkdir -p /home/user/profilesvc/internal/db

RUN cat > /home/user/profilesvc/go.mod << 'EOF'
module profilesvc

go 1.21
EOF

RUN cat > /home/user/profilesvc/config.yaml << 'EOF'
port: 8080
startup_timeout: 5s
cache_warmup: true
warmup_endpoint: "http://localhost:9999/warmup"
db_pool_size: 10
service_name: "profilesvc"
EOF

RUN cat > /home/user/profilesvc/internal/cache/cache.go << 'EOF'
package cache

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"
)

var (
	initialized bool
	initError   error
	mu          sync.RWMutex
)

type Config interface {
	GetCacheWarmup() bool
	GetWarmupEndpoint() string
	GetStartupTimeout() time.Duration
}

func Init(cfg Config) error {
	mu.Lock()
	defer mu.Unlock()

	if !cfg.GetCacheWarmup() {
		initialized = true
		initError = nil
		return nil
	}

	endpoint := cfg.GetWarmupEndpoint()
	// BUG: ignores the startup_timeout from config and uses hardcoded 30s
	// The context with cfg.GetStartupTimeout() is created but not used properly
	_ = cfg.GetStartupTimeout() // pretend we use it

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, "GET", endpoint, nil)
	if err != nil {
		initError = fmt.Errorf("failed to create warmup request: %w", err)
		initialized = false
		return initError
	}

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		initError = fmt.Errorf("cache warmup failed: %w", err)
		initialized = false
		return initError
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		initError = fmt.Errorf("cache warmup returned status %d", resp.StatusCode)
		initialized = false
		return initError
	}

	initialized = true
	initError = nil
	return nil
}

func MustBeReady() {
	mu.RLock()
	defer mu.RUnlock()

	if !initialized || initError != nil {
		panic(fmt.Sprintf("cache not properly initialized: %v", initError))
	}
}

func IsReady() bool {
	mu.RLock()
	defer mu.RUnlock()
	return initialized && initError == nil
}
EOF

RUN cat > /home/user/profilesvc/internal/db/db.go << 'EOF'
package db

import (
	"fmt"
	"os"

	"profilesvc/internal/cache"
)

type Config interface {
	GetDBPoolSize() int
}

var poolSize int

func Init(cfg Config) (err error) {
	// Added after "cleanup" - require cache to be ready before DB init
	// This was added to ensure proper initialization order
	defer func() {
		if r := recover(); r != nil {
			fmt.Fprintf(os.Stderr, "db init panic: %v\n", r)
			os.Exit(1)
		}
	}()

	// This will panic if cache init failed
	cache.MustBeReady()

	poolSize = cfg.GetDBPoolSize()
	if poolSize <= 0 {
		poolSize = 5
	}

	// Mock DB initialization - no real database needed
	fmt.Printf("db pool initialized with size %d\n", poolSize)
	return nil
}

func GetPoolSize() int {
	return poolSize
}
EOF

RUN cat > /home/user/profilesvc/main.go << 'EOF'
package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"gopkg.in/yaml.v3"

	"profilesvc/internal/cache"
	"profilesvc/internal/db"
)

type Config struct {
	Port           int           `yaml:"port"`
	StartupTimeout time.Duration `yaml:"startup_timeout"`
	CacheWarmup    bool          `yaml:"cache_warmup"`
	WarmupEndpoint string        `yaml:"warmup_endpoint"`
	DBPoolSize     int           `yaml:"db_pool_size"`
	ServiceName    string        `yaml:"service_name"`
}

func (c *Config) GetCacheWarmup() bool {
	return c.CacheWarmup
}

func (c *Config) GetWarmupEndpoint() string {
	return c.WarmupEndpoint
}

func (c *Config) GetStartupTimeout() time.Duration {
	return c.StartupTimeout
}

func (c *Config) GetDBPoolSize() int {
	return c.DBPoolSize
}

func loadConfig(path string) *Config {
	data, err := os.ReadFile(path)
	if err != nil {
		log.Fatalf("failed to read config: %v", err)
	}

	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		log.Fatalf("failed to parse config: %v", err)
	}

	if cfg.Port == 0 {
		cfg.Port = 8080
	}

	return &cfg
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("ok"))
}

func main() {
	cfg := loadConfig("config.yaml")

	log.Printf("starting %s initialization...", cfg.ServiceName)

	if err := cache.Init(cfg); err != nil {
		log.Printf("cache init failed: %v", err)
	}

	if err := db.Init(cfg); err != nil {
		log.Fatalf("db init failed: %v", err)
	}

	http.HandleFunc("/health", healthHandler)

	addr := fmt.Sprintf(":%d", cfg.Port)
	log.Printf("starting server on %s", addr)
	log.Fatal(http.ListenAndServe(addr, nil))
}
EOF

WORKDIR /home/user/profilesvc

RUN go mod tidy

RUN chmod -R 0777 /home/user

WORKDIR /home/user

CMD ["/bin/bash"]
