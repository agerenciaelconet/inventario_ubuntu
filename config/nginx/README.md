````markdown
# Configuración de Nginx para proyecto Django

Este archivo describe los pasos necesarios para configurar Nginx como servidor web para el proyecto Django.

---

## 🔧 Pasos para la configuración

### 1. Copiar el archivo de configuración de Nginx

```bash
sudo cp /ruta/a/config/nginx/archivo.conf /etc/nginx/sites-available/
````

> Reemplazar `/ruta/a/` con la ruta real donde esté el archivo `.conf`.

---

### 2. Activar el sitio en Nginx

```bash
sudo ln -s /etc/nginx/sites-available/archivo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

> Asegúrate de que el nombre del archivo en sites-enabled/ coincida exactamente con el de sites-available/, incluyendo o no la extensión .conf, según cómo lo hayas nombrado originalmente.

---

### 3. Dar permisos de lectura a los archivos estáticos

```bash
sudo chmod -R o+r /ruta/a/staticfiles
sudo chmod -R o+X /ruta/a/staticfiles
sudo chmod o+x /ruta/a/
sudo chmod o+x /ruta/a/staticfiles
```

> Reemplazar `/ruta/a/staticfiles` por la ubicación real del directorio `staticfiles`.

## ✅ Notas adicionales

* Antes de hacer esta configuración, asegurate de haber ejecutado `python manage.py collectstatic`.
* El bloque `location /static/` en la configuración Nginx debe tener un `alias` que apunte al directorio `staticfiles`.
* Esta configuración es solo para servir archivos estáticos. Django debe ejecutarse por WSGI (por ejemplo, usando Gunicorn o uWSGI).
