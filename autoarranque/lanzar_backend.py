#!/usr/bin/env python3
import subprocess
import time
import logging
import requests
import sys
import socket
import os

# Ruta absoluta al script bash que se ejecutará para iniciar el servidor
# Reemplazar con la ubicación real del archivo iniciar_servidor.sh
SCRIPT_BASH = "/ruta/a/iniciar_servidor.sh"
TELEGRAM_FLAG_FILE = "/tmp/telegram_notify_sent.flag"

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def verificar_nginx_activo(reintentos=10, espera=3):
    for intento in range(reintentos):
        try:
            with socket.create_connection(("127.0.0.1", 80), timeout=2):
                logging.info("✅ Nginx está activo y escuchando en el puerto 80.")
                return True
        except (OSError, socket.timeout):
            logging.warning(f"⏳ [{intento+1}/{reintentos}] Nginx no está activo aún. Esperando {espera}s...")
            time.sleep(espera)
    logging.error("❌ Nginx no se activó tras múltiples intentos.")
    return False

def verificar_conexion_internet(reintentos=5, espera=5):
    for intento in range(reintentos):
        try:
            requests.get("https://8.8.8.8", timeout=3)
            logging.info("✅ Conexión a internet verificada.")
            return True
        except Exception:
            logging.warning(f"🌐 [{intento+1}/{reintentos}] Sin internet. Esperando {espera}s...")
            time.sleep(espera)
    logging.warning("⚠️ No hay internet tras varios intentos. Continuando en modo local.")
    return False

def enviar_mensaje_telegram_si_es_necesario():
    if not os.path.exists(TELEGRAM_FLAG_FILE):
        try:
            ip_local = socket.gethostbyname(socket.gethostname())
            mensaje = f"🚀 Servidor Django con Gunicorn iniciado\n🔗 IP local: http://{ip_local}"
            logging.info(mensaje)

            open(TELEGRAM_FLAG_FILE, "w").close()
        except Exception as e:
            logging.error(f"❌ No se pudo enviar mensaje a Telegram: {e}")

def ejecutar_script_bash():
    try:
        logging.info(f"🚀 Ejecutando script: {SCRIPT_BASH}")
        proceso = subprocess.Popen(
            ["/bin/bash", SCRIPT_BASH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logging.info("✅ Script lanzado exitosamente.")
        return proceso
    except Exception as e:
        logging.error(f"❌ Error al lanzar el script: {e}")
        return None

if __name__ == "__main__":
    logging.info("📦 Arranque del backend iniciado.")

    if not verificar_nginx_activo():
        logging.error("🛑 Abortando inicio. Nginx no está activo.")
        sys.exit(1)

    verificar_conexion_internet()
    enviar_mensaje_telegram_si_es_necesario()

    proceso = ejecutar_script_bash()
    if proceso:
        logging.info("✅ Script bash iniciado, esperando indefinidamente para evitar reinicio...")
        while True:
            time.sleep(60)
    else:
        logging.error("❌ No se pudo iniciar el script. Saliendo.")
        sys.exit(1)

