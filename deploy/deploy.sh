#!/bin/bash
set -e

echo "=== Sentry Deploy Script ==="

# Настройка nginx
echo "[1/4] Настраиваю nginx..."
sudo apt install -y -qq nginx
sudo cp ~/sentry/deploy/nginx/sentry.conf /etc/nginx/sites-available/sentry
sudo ln -sf /etc/nginx/sites-available/sentry /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
echo "Nginx настроен на порту 8091"

# Настройка self-hosted конфигов (не перезаписываем secret-key и другие локальные настройки)
echo "[2/4] Обновляю конфиги..."
sudo cp ~/sentry/self-hosted/sentry.conf.py ~/self-hosted/sentry/sentry.conf.py

# Пересборка образа (чтобы новый sentry.conf.py попал в контейнер)
echo "[3/4] Пересобираю образ..."
cd ~/self-hosted
sudo docker compose build web

# Перезапуск Sentry
echo "[4/4] Перезапускаю Sentry..."
sudo docker compose up -d

echo "=== Готово! Sentry доступен на http://sentry.gram.tj:8091 ==="
