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

# Сборка и запуск контейнеров
echo "[3/4] Собираю и запускаю Sentry..."
cd ~/self-hosted
sudo docker compose build web
if [ -f .env.custom ]; then
    sudo docker compose --env-file .env --env-file .env.custom up -d
else
    sudo docker compose up -d
fi

# Копируем кастомные плагины из ~/sentry в контейнеры
# (образ базируется на ghcr.io/getsentry/sentry, наши плагины нужно добавлять отдельно)
echo "[4/4] Обновляю кастомные плагины..."
PLUGIN_SRC=~/sentry/src/sentry_plugins/telegram
PLUGIN_DST=/usr/src/sentry/src/sentry_plugins/telegram

for service in web worker cron taskworker; do
    container=$(sudo docker compose ps -q "$service" 2>/dev/null)
    if [ -n "$container" ]; then
        sudo docker compose cp "$PLUGIN_SRC/." "$service:$PLUGIN_DST/"

        # Регистрируем Telegram плагин в entry_points.txt (egg-info), если ещё не добавлен
        sudo docker compose exec -T "$service" sh -c '
            EP=/usr/src/sentry/src/sentry.egg-info/entry_points.txt
            if ! grep -q "telegram = sentry_plugins.telegram.plugin:TelegramPlugin" "$EP"; then
                sed -i "/victorops = sentry_plugins.victorops.plugin:VictorOpsPlugin/a telegram = sentry_plugins.telegram.plugin:TelegramPlugin" "$EP"
            fi
        '

        echo "  -> $service: плагин скопирован + entry point зарегистрирован"
    fi
done

sudo docker compose restart web taskworker
echo "  -> web, taskworker перезапущены"

echo "=== Готово! Sentry доступен на http://sentry.gram.tj:8091 ==="
