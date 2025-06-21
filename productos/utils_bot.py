import requests
from django.conf import settings

def enviar_respuesta_telegram(chat_id, mensaje):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=payload)
    return response.json()
