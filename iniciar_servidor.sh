#!/bin/bash

# === RUTAS ===
PROYECTO_DIR="/home/$USER/django-server"
ENTORNO_VIRTUAL="$PROYECTO_DIR/env/bin/activate"
NGROK_BIN="/usr/local/bin/ngrok"
GUNICORN_BIN="$PROYECTO_DIR/env/bin/gunicorn"

# === VARIABLES DEL BOT ===
BOT_TOKEN="7612438597:AAFWnvkBsJzO-2_wNnhvmSE7zaM8WwO6UbI"
CHAT_ID=-4886039686
WEBHOOK_ENDPOINT="/productos/webhook/"

# === FUNCIÓN PARA OBTENER IP LOCAL ===
get_local_ip() {
    hostname -I | awk '{print $1}'
}

# === FUNCIÓN PARA ENVIAR MENSAJE A TELEGRAM ===
send_telegram_msg() {
    local ip="$1"
    local msg="🚀 Servidor Django con Gunicorn iniciado%0A🔗 IP local: http://${ip}"
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d "chat_id=${CHAT_ID}" \
        -d "text=${msg}" \
        -d "disable_notification=false"
}

# === INICIO DEL SCRIPT ===

# PASO 1: Activar entorno y ejecutar Gunicorn
cd "$PROYECTO_DIR"
source "$ENTORNO_VIRTUAL"
$GUNICORN_BIN --workers 4 --bind 127.0.0.1:8000 inventario.wsgi:application &
sleep 3

# PASO 2: Ejecutar ngrok
deactivate
"$NGROK_BIN" http 8000 > /dev/null &
sleep 5

# PASO 3: Configurar webhook
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[a-zA-Z0-9.-]*\.ngrok-free\.app' | head -n 1)

if [ -z "$NGROK_URL" ]; then
  echo "❌ No se pudo obtener la URL pública de ngrok. Verifica que ngrok esté instalado y activo."
  exit 1
fi

FULL_WEBHOOK="${NGROK_URL}${WEBHOOK_ENDPOINT}"
echo "🌐 Webhook completo: $FULL_WEBHOOK"

# PASO 4: Enviar webhook a Telegram
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" -d "url=${FULL_WEBHOOK}"

# PASO 5: Iniciar Celery
cd "$PROYECTO_DIR"
source "$ENTORNO_VIRTUAL"
celery -A inventario worker -l info &

# === ENVÍO DE NOTIFICACIÓN FINAL ===
LOCAL_IP=$(get_local_ip)
send_telegram_msg "$LOCAL_IP"

echo "✅ Servidor iniciado con Gunicorn. Notificación enviada a Telegram."
