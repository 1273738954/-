# syntax=docker/dockerfile:1

# ---------- 1. 构建前端 ----------
FROM node:22-alpine AS frontend
WORKDIR /app/frontend
ARG NPM_REGISTRY=https://registry.npmmirror.com
COPY frontend/package.json frontend/package-lock.json ./
RUN npm config set registry "$NPM_REGISTRY" && npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---------- 2. 构建后端 ----------
FROM golang:1.25.5-alpine AS backend
WORKDIR /app/backend
ARG GOPROXY=https://goproxy.cn,direct
ENV CGO_ENABLED=0 GOOS=linux GOARCH=amd64 GOPROXY=${GOPROXY}
COPY backend/go.mod backend/go.sum ./
RUN go mod download
COPY backend/ ./
RUN go build -ldflags="-s -w" -o /out/ninimenu ./cmd/server

# ---------- 3. 运行时 ----------
FROM alpine:3.20
WORKDIR /app
RUN apk add --no-cache ca-certificates tzdata
ENV TZ=Asia/Shanghai PORT=8080

COPY --from=backend /out/ninimenu /app/ninimenu
COPY --from=frontend /app/frontend/dist /app/static
# 内置一份菜品图片种子，首次启动自动铺到 /app/uploads
COPY backend/uploads /app/seed-uploads
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

RUN chmod +x /app/ninimenu /app/docker-entrypoint.sh \
    && mkdir -p /app/data /app/uploads /app/uploads_backup

EXPOSE 8080
VOLUME ["/app/data", "/app/uploads", "/app/uploads_backup"]
ENTRYPOINT ["/app/docker-entrypoint.sh"]
