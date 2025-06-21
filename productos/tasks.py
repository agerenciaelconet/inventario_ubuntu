from celery import shared_task
from .utils_bot import enviar_respuesta_telegram
from django.conf import settings

@shared_task
def enviar_mensaje_telegram(chat_id, mensaje):
    # Llama a la función para enviar el mensaje
    response = enviar_respuesta_telegram(chat_id, mensaje)
    
    # Opcional: manejar la respuesta de la API de Telegram si es necesario
    if response.get("ok"):
        return "Mensaje enviado exitosamente."
    else:
        return f"Error al enviar el mensaje: {response.get('description')}"
