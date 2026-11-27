#!/bin/bash

set -e

echo "🧹 Cleaning Docker..."
docker compose down || true
docker system prune -af --volumes

echo "🔨 Building Docker image (no cache)..."
docker compose build --no-cache

echo "🚀 Starting Docker..."
docker compose up -d

echo "✅ Done! Bot restarted with fresh build."
