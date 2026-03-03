#!/bin/bash
set -e

echo "=== Откат на официальный Sentry ==="

cd ~/self-hosted
sudo git checkout docker-compose.yml
sudo docker compose up -d

echo "=== Готово! Переключено на официальный образ ==="
