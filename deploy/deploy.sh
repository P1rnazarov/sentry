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

# НЕ перезаписываем серверные конфиги (sentry.conf.py, config.yml, .env.custom)
# Они настроены на сервере вручную и содержат секреты
echo "[2/3] Конфиги сервера не трогаем (настроены вручную)"

# Перезапуск Sentry с двумя env-файлами
echo "[3/3] Перезапускаю Sentry..."
cd ~/self-hosted
if [ -f .env.custom ]; then
    sudo docker compose --env-file .env --env-file .env.custom up -d
else
    sudo docker compose up -d
fi

echo "=== Готово! Sentry доступен на http://sentry.gram.tj:8091 ==="
