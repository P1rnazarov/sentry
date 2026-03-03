#!/bin/bash
set -e

echo "=== Sentry Deploy Script ==="

# Настройка nginx
echo "[1/3] Настраиваю nginx..."
sudo apt install -y -qq nginx
sudo cp ~/sentry/deploy/nginx/sentry.conf /etc/nginx/sites-available/sentry
sudo ln -sf /etc/nginx/sites-available/sentry /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
echo "Nginx настроен на порту 8091"

# Настройка self-hosted конфигов
echo "[2/3] Обновляю конфиги..."
if [ -f ~/sentry/self-hosted/sentry.conf.py ]; then
    sudo cp ~/sentry/self-hosted/sentry.conf.py ~/self-hosted/sentry/sentry.conf.py 2>/dev/null || true
fi
if [ -f ~/sentry/self-hosted/config.yml ]; then
    sudo cp ~/sentry/self-hosted/config.yml ~/self-hosted/sentry/config.yml 2>/dev/null || true
fi

# Перезапуск Sentry
echo "[3/3] Перезапускаю Sentry..."
cd ~/self-hosted
sudo docker compose up -d

echo "=== Готово! Sentry доступен на http://sentry.gram.tj:8091 ==="
