import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
from .models import Producto
from .tasks import enviar_mensaje_telegram

@csrf_exempt
def telegram_webhook(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        message = data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")

        if not chat_id or not text:
            return JsonResponse({"ok": True})

        if text.startswith("/stock"):
            partes = text.split()
            if len(partes) == 2:
                codigo = partes[1].strip()
                try:
                    producto = Producto.objects.get(codigo=codigo)
                    mensaje = f"📦`{producto.codigo}` - *{producto.nombre}*\nStock actual: `{producto.cantidad}` unidades"
                except Producto.DoesNotExist:
                    mensaje = f"❌ Producto con código `{codigo}` no encontrado."
            else:
                mensaje = "⚠️ Uso correcto: `/stock <código>`"

        elif text.startswith("/alertas"):
            productos = Producto.objects.filter(alerta_activa=True, cantidad__lte=F("alerta_stock"))
            if productos.exists():
                mensaje = "*📉 Productos en alerta de stock:*\n"
                for p in productos:
                    mensaje += (f"- `{p.codigo}` - {p.nombre}: `{p.cantidad}` unidades\n"
                                f"*Stock recomendado*: `{p.alerta_stock}` unidades\n\n")
            else:
                mensaje = "✅ No hay productos en alerta de stock."

        else:
            mensaje = "🤖 Comandos disponibles:\n/stock <código>\n/alertas"

        enviar_mensaje_telegram.delay(chat_id, mensaje)
        return JsonResponse({"ok": True})
    return JsonResponse({"status": "Método no permitido"}, status=405)
