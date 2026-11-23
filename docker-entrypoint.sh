#!/bin/sh
set -e

# 首次启动时，如果 uploads 目录为空，则铺入镜像内置的菜品图片，
# 保证数据库里 /uploads/xxx.webp 这类图片路径能正常访问。
if [ -z "$(ls -A /app/uploads 2>/dev/null)" ]; then
  echo "[init] seeding dish images into /app/uploads ..."
  cp -a /app/seed-uploads/. /app/uploads/ 2>/dev/null || true
fi

mkdir -p /app/data /app/uploads_backup

echo "[init] starting ninimenu on port ${PORT:-8080}"
exec /app/ninimenu
