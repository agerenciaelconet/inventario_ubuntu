from django.urls import path
from .views import lista_productos, agregar_producto, gestionar_producto, historial_movimientos, lista_ubicaciones, agregar_ubicacion, editar_ubicacion, eliminar_ubicacion, exportar_historial_excel, exportar_historial_pdf, exportar_productos_excel, exportar_productos_pdf
from .bot_webhook import telegram_webhook


urlpatterns = [
    path("", lista_productos, name="lista_productos"),  # Página principal con la lista de productos
    path("agregar/", agregar_producto, name="agregar_producto"),
    path("producto/<int:producto_id>/gestionar/", gestionar_producto, name="gestionar_producto"),  # Nueva ruta
    path("historial/", historial_movimientos, name="historial_movimientos"),
    path("webhook/", telegram_webhook, name="webhook"),
# Rutas para gestión de ubicaciones
    path("ubicaciones/", lista_ubicaciones, name="lista_ubicaciones"),
    path("ubicaciones/agregar/", agregar_ubicacion, name="agregar_ubicacion"),
    path("ubicaciones/<int:ubicacion_id>/editar/", editar_ubicacion, name="editar_ubicacion"),
    path("ubicaciones/<int:ubicacion_id>/eliminar/", eliminar_ubicacion, name="eliminar_ubicacion"),
    path('historial/exportar_excel/', exportar_historial_excel, name='exportar_historial_excel'),
    path('historial/exportar_pdf/', exportar_historial_pdf, name='exportar_historial_pdf'),
    path('productos/exportar_excel/', exportar_productos_excel, name='exportar_productos_excel'),
    path('productos/exportar_pdf/', exportar_productos_pdf, name='exportar_productos_pdf'),
]
