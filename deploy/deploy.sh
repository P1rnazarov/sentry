#!/bin/bash
set -e

echo "=== Sentry Deploy Script ==="

# Настройка nginx
echo "[1/4] Настраиваю nginx..."
sudo apt install -y nginx
sudo cp deploy/nginx/sentry.conf /etc/nginx/sites-available/sentry
sudo ln -sf /etc/nginx/sites-available/sentry /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
echo "Nginx настроен на порту 8091"

# Сборка кастомного образа
echo "[2/4] Собираю Docker-образ..."
sudo docker build -f self-hosted/Dockerfile -t sentry-custom .

# Подмена образа в self-hosted
echo "[3/4] Переключаю self-hosted на кастомный образ..."
cd ~/self-hosted
sudo sed -i "s|image: .*sentry-self-hosted-local.*|image: sentry-custom|g" docker-compose.yml

# Перезапуск
echo "[4/4] Перезапускаю Sentry..."
sudo docker compose up -d

echo "=== Готово! Sentry доступен на http://sentry.gram.tj:8091 ==="
