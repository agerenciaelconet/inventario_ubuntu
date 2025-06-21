#!/bin/bash
echo "🛑 Deteniendo servidor Gunicorn, Ngrok, Celery y servicio systemd..."

# 1. Detener el servicio systemd (si lo estás usando y está activo)
if sudo systemctl is-active --quiet mi_servidor.service; then
    echo "▸ Deteniendo mi_servidor.service..."
    sudo systemctl stop mi_servidor.service
fi

# 2. Matar procesos manuales (por si se iniciaron sin systemd)
echo "▸ Matando procesos restantes..."
pkill -f "gunicorn"
pkill -f "ngrok"
pkill -f "celery"

# 3. Verificación final
if pgrep -f "gunicorn" || pgrep -f "ngrok" || pgrep -f "celery"; then
    echo "⚠️ Algunos procesos no se detuvieron. Forzando cierre..."
    pkill -9 -f "gunicorn"
    pkill -9 -f "ngrok"
    pkill -9 -f "celery"
fi

echo "✅ Todo detenido (servicio + procesos manuales)."
