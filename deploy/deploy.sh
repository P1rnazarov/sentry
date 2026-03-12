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

# НЕ перезаписываем серверные конфиги (sentry.conf.py, config.yml, .env.custom)
# Они настроены на сервере вручную и содержат секреты
echo "[2/4] Конфиги сервера не трогаем (настроены вручную)"

# Синхронизируем код из ~/sentry в ~/self-hosted для сборки Docker образа
# (docker compose build использует ~/self-hosted как контекст, а git pull обновляет ~/sentry)
echo "[3/4] Синхронизирую исходный код..."
rsync -a \
    --exclude='.git' \
    --exclude='.env' \
    --exclude='.env.custom' \
    --exclude='docker-compose*.yml' \
    ~/sentry/ ~/self-hosted/

# Сборка и перезапуск Sentry с двумя env-файлами
echo "[4/4] Собираю и перезапускаю Sentry..."
cd ~/self-hosted
sudo docker compose build --no-cache web
if [ -f .env.custom ]; then
    sudo docker compose --env-file .env --env-file .env.custom up -d
else
    sudo docker compose up -d
fi

echo "=== Готово! Sentry доступен на http://sentry.gram.tj:8091 ==="
