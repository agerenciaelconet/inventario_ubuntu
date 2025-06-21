#!/usr/bin/env python3

import requests
import socket
import time
import getpass

# CREDENCIALES DE TELEGRAM (MODIFICAR CON TUS DATOS REALES)
TOKEN = "TU_TOKEN_AQUI"
CHAT_ID = "TU_CHAT_ID_AQUI"

def verificar_conexion_internet(reintentos=5, espera=5):
    for intento in range(reintentos):
        try:
            requests.get("https://8.8.8.8", timeout=3)
            return True
        except requests.RequestException:
            print(f"[{intento+1}/{reintentos}] No hay conexión. Reintentando en {espera}s...")
            time.sleep(espera)
    return False

def obtener_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip_local = s.getsockname()[0]
    except Exception:
        ip_local = 'No se pudo obtener la IP'
    finally:
        s.close()
    return ip_local

def enviar_mensaje(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Error al enviar mensaje: {e}")

if __name__ == "__main__":
    if verificar_conexion_internet():
        ip = obtener_ip_local()
        usuario = getpass.getuser()
        host = socket.gethostname()
        mensaje = (
            f"🚀 Raspberry iniciada\n"
            f"👤 Usuario: {usuario}@{host}.local\n"
            f"🔗 IP local: http://{ip}"
        )
        enviar_mensaje(mensaje)
    else:
        print("❌ No se pudo establecer conexión a internet. No se envió la IP.")
