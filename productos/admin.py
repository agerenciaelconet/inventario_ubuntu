from django.contrib import admin
from .models import Producto, MovimientoInventario, Ubicacion

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'cantidad', 'alerta_stock', 'alerta_activa', 'activo')
    list_filter = ('alerta_activa', 'activo',)
    search_fields = ('nombre', 'codigo')


class MovimientoInventarioAdmin(admin.ModelAdmin):
    readonly_fields = ('nombre_producto',)
    list_display = ('producto', 'tipo', 'cantidad', 'fecha', 'comentario')
    list_filter = ('tipo', 'fecha')
    search_fields = ('producto__nombre', 'comentario')


class UbicacionAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


admin.site.register(Producto, ProductoAdmin)
admin.site.register(MovimientoInventario, MovimientoInventarioAdmin)
admin.site.register(Ubicacion, UbicacionAdmin)
