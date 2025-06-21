from django.db import models
from django.conf import settings
from .tasks import enviar_mensaje_telegram
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User


class Ubicacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        # Normaliza el nombre (todo minúscula, sin espacios extra)
        self.nombre = self.nombre.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)  # Nombre del producto
    cantidad = models.IntegerField(default=0, validators=[MinValueValidator(0)])  # Cantidad disponible
    alerta_stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])  # Límite de stock para alerta
    alerta_activa = models.BooleanField(default=False)  # Si la alerta está activada o no
    codigo = models.CharField(max_length=10, unique=True, blank=True)  # Código del producto
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, blank=True, null=True)
    activo = models.BooleanField(default=True)


    def save(self, *args, **kwargs):
        # Solo asignar el código si no tiene uno asignado
        if not self.codigo:
            last_codigo = Producto.objects.all().order_by('id').last()
            if last_codigo:
                # Si existe un producto, incrementar el número
                new_codigo = f'P-{int(last_codigo.codigo.split("-")[1]) + 1:04d}'
            else:
                # Si no existe ningún producto, iniciar con P-0001
                new_codigo = 'P-0001'
            self.codigo = new_codigo

        # Validar que el código no sea modificado una vez asignado
        if self.pk is not None:
            original = Producto.objects.get(pk=self.pk)
            if original.codigo != self.codigo:
                raise ValueError("No se puede modificar el código una vez asignado.")

        # Verificar si es necesario enviar la alerta de stock
        if self.necesita_alerta():
            mensaje = f"*¡Alerta de stock bajo!*\nEl producto `\"{self.codigo} - {self.nombre}\"` ha alcanzado el límite de stock.\nUnidades actuales: `{self.cantidad}`\nStock mínimo recomendado: `{self.alerta_stock}`"
            enviar_mensaje_telegram.delay(settings.TELEGRAM_CHAT_ID, mensaje)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    def necesita_alerta(self):
        # Solo verifica si necesita alerta si está activada
        if self.alerta_activa:
            return self.cantidad <= self.alerta_stock
        return False


class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO = [
        ("entrada", "Entrada"),
        ("salida", "Salida"),
    ]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    nombre_producto = models.CharField(max_length=100, default='')
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    fecha = models.DateTimeField(auto_now_add=True)
    comentario = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.nombre_producto:
            self.nombre_producto = self.producto.nombre
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.tipo.capitalize()} de {self.cantidad} - {self.nombre_producto}"
