from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Establecer el módulo de configuración de Django por defecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario.settings')

app = Celery('inventario')

# Leer configuración desde settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descubrir tareas automáticamente dentro de apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
