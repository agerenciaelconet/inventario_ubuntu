from django.shortcuts import render, redirect
from django.db.models import Q, F
from .models import Producto, MovimientoInventario, Ubicacion
from .forms import MovimientoInventarioForm, ProductoForm, UbicacionForm
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import datetime
import json, re
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.models import User
from django.core.paginator import Paginator
# Exportar Excel
import xlsxwriter
from django.http import HttpResponse
from io import BytesIO
# Exportar PDF
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO


# Función de prueba para verificar si el usuario pertenece al grupo 'administrador'
def es_administrador(user):
    return user.groups.filter(name='Administrador').exists()

# Función de prueba para verificar si el usuario pertenece al grupo 'supervisor'
def es_supervisor(user):
    return user.groups.filter(name='Supervisor').exists()

# Función de prueba para verificar si el usuario pertenece al grupo 'almacén'
def es_almacen(user):
    return user.groups.filter(name='Almacen').exists()

# Función de prueba para verificar si el usuario pertenece al grupo 'técnico'
def es_tecnico(user):
    return user.groups.filter(name='Tecnico').exists()


@login_required
def lista_productos(request):
    query = request.GET.get("q", "").strip()
    ubicacion = request.GET.get("ubicacion", "").strip()
    cantidad_filtro = request.GET.get("cantidad_filtro", "").strip()
    estado_activo = request.GET.get("estado_activo", "")
    alerta = request.GET.get("alerta", "")

    productos = filtrar_productos(request)

    ubicaciones_disponibles = Ubicacion.objects.all().order_by('nombre')

    # Paginacion
    paginator = Paginator(productos, 15)  # Mostrará 15 productos por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "productos/lista_productos.html", {
        "productos": page_obj,
        "page_obj": page_obj,
        "query": query,
        "ubicacion": ubicacion,
        "cantidad_filtro": cantidad_filtro,
        "estado_activo": estado_activo,
        "alerta": alerta,
        "ubicaciones_disponibles": ubicaciones_disponibles,
    })


@login_required
@user_passes_test(lambda user: es_administrador(user) or es_supervisor(user), login_url='/usuarios/login/')
def agregar_producto(request):
    if request.method == "POST":
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()  # Guardamos el nuevo producto
            comentario = form.cleaned_data.get('comentario')  # Obtenemos el comentario

            MovimientoInventario.objects.create(
                producto=producto,
                tipo="entrada",
                cantidad=producto.cantidad,  # En este caso la cantidad es la cantidad inicial del producto
                comentario=comentario,  # Guardamos el comentario en el movimiento
                usuario=request.user
            )

            return redirect('lista_productos')  # Redirigimos a la lista de productos
    else:
        form = ProductoForm()

    return render(request, 'productos/agregar_producto.html', {'form': form})


@login_required
def gestionar_producto(request, producto_id):
    producto = Producto.objects.get(id=producto_id)

    movimientos_queryset = MovimientoInventario.objects.filter(producto=producto).order_by("-fecha")
    paginator = Paginator(movimientos_queryset, 5)  # Cambia 10 por la cantidad que desees por página
    page_number = request.GET.get("page")
    movimientos = paginator.get_page(page_number)


    # Inicializamos formularios por defecto
    movimiento_form = MovimientoInventarioForm(initial={"producto": producto})
    producto_form = ProductoForm(instance=producto)

    if request.method == "POST":
        if 'movimiento' in request.POST:
            # Verificamos permisos para movimientos
            if not (es_administrador(request.user) or es_supervisor(request.user) or es_almacen(request.user)):
                # No tiene permiso, se renderiza con formularios ya inicializados
                return render(request, "productos/gestionar_producto.html", {
                    "producto_form": producto_form,
                    "producto": producto,
                    "movimientos": page_obj,
                    "movimiento_form": movimiento_form,
                })

            movimiento_form = MovimientoInventarioForm(request.POST)

            if movimiento_form.is_valid():
                if not producto.activo:
                    movimiento_form.add_error(None, "Este producto está desactivado y no se pueden registrar movimientos.")
                else:
                    movimiento = movimiento_form.save(commit=False)
                    movimiento.producto = producto
                    movimiento.usuario = request.user

                    if movimiento.tipo == "entrada":
                        producto.cantidad += movimiento.cantidad
                    elif movimiento.tipo == "salida":
                        if producto.cantidad >= movimiento.cantidad:
                            producto.cantidad -= movimiento.cantidad
                        else:
                            movimiento_form.add_error("cantidad", "No hay suficiente stock disponible")
                            return render(request, "productos/gestionar_producto.html", {
                                "movimiento_form": movimiento_form,
                                "producto_form": producto_form,
                                "producto": producto,
                                "movimientos": movimientos
                            })

                    producto.save()
                    movimiento.save()
                    return redirect("gestionar_producto", producto_id=producto.id)

        elif 'editar' in request.POST:
            # Verificamos permisos para edición
            if not (es_administrador(request.user) or es_supervisor(request.user)):
                return render(request, "productos/gestionar_producto.html", {
                    "movimiento_form": movimiento_form,
                    "producto_form": producto_form,
                    "producto": producto,
                    "movimientos": movimientos
                })

            producto_form = ProductoForm(request.POST, instance=producto)
            if producto_form.is_valid():
                producto_form.save()
                return redirect("gestionar_producto", producto_id=producto.id)

    # Render final único con formularios (válidos o no)
    return render(request, "productos/gestionar_producto.html", {
        "movimiento_form": movimiento_form,
        "producto_form": producto_form,
        "producto": producto,
        "movimientos": movimientos
    })



@login_required
def historial_movimientos(request):
    query = request.GET.get("q", "").strip()
    tipo = request.GET.get("tipo")
    fecha_filtro = request.GET.get("fecha_filtro", "").strip()
    movimientos, error_fecha = filtrar_movimientos(request)

    # Paginación
    paginator = Paginator(movimientos, 20)  # 20 por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)


    return render(request, "productos/historial_movimientos.html", {
        "movimientos": page_obj,
        "page_obj": page_obj,
        "query": query,
        "fecha_filtro": fecha_filtro,
        "error_fecha": error_fecha,
    })


@login_required
@user_passes_test(lambda user: es_administrador(user) or es_supervisor(user), login_url='/usuarios/login/')
def lista_ubicaciones(request):
    ubicaciones = Ubicacion.objects.all().order_by("nombre")
    return render(request, "productos/lista_ubicaciones.html", {"ubicaciones": ubicaciones})


@login_required
@user_passes_test(lambda user: es_administrador(user) or es_supervisor(user), login_url='/usuarios/login/')
def agregar_ubicacion(request):
    if request.method == "POST":
        form = UbicacionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("lista_ubicaciones")
    else:
        form = UbicacionForm()
    return render(request, "productos/agregar_ubicacion.html", {"form": form, "modo": "Agregar"})


@login_required
@user_passes_test(lambda user: es_administrador(user) or es_supervisor(user), login_url='/usuarios/login/')
def editar_ubicacion(request, ubicacion_id):
    ubicacion = Ubicacion.objects.get(id=ubicacion_id)
    if request.method == "POST":
        form = UbicacionForm(request.POST, instance=ubicacion)
        if form.is_valid():
            form.save()
            return redirect("lista_ubicaciones")
    else:
        form = UbicacionForm(instance=ubicacion)
    return render(request, "productos/editar_ubicacion.html", {"form": form, "modo": "Editar"})

@login_required
@user_passes_test(lambda user: es_administrador(user) or es_supervisor(user), login_url='/usuarios/login/')
def eliminar_ubicacion(request, ubicacion_id):
    ubicacion = Ubicacion.objects.get(id=ubicacion_id)
    if request.method == "POST":
        ubicacion.delete()
        return redirect("lista_ubicaciones")
    return render(request, "productos/eliminar_ubicacion.html", {"ubicacion": ubicacion})


@login_required
def exportar_historial_excel(request):
    movimientos = filtrar_movimientos(request)[0]
    print(movimientos)
    # Crear archivo en memoria
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet("Historial")

    # Estilos opcionales
    bold = workbook.add_format({'bold': True})
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm'})

    # Cabeceras
    headers = ["Fecha", "Producto", "Código", "Tipo", "Cantidad", "Usuario", "Comentario"]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, bold)

    # Filas
    for row, m in enumerate(movimientos, start=1):
        worksheet.write(row, 0, m.fecha.replace(tzinfo=None), date_format)
        worksheet.write(row, 1, m.producto.nombre)
        worksheet.write(row, 2, m.producto.codigo)
        worksheet.write(row, 3, m.tipo)
        worksheet.write(row, 4, m.cantidad)
        worksheet.write(row, 5, str(m.usuario))
        worksheet.write(row, 6, m.comentario)

    workbook.close()
    output.seek(0)

    # Respuesta HTTP para descarga
    response = HttpResponse(output.read(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="historial_movimientos.xlsx"'
    return response


@login_required
def exportar_historial_pdf(request):
    movimientos = filtrar_movimientos(request)[0]

    # Renderizar plantilla HTML a PDF
    template = get_template("productos/pdf_historial.html")
    html = template.render({"movimientos": movimientos})
    output = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=output)

    if pisa_status.err:
        return HttpResponse("Error al generar PDF", status=500)

    response = HttpResponse(output.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="historial_movimientos.pdf"'
    return response


def filtrar_movimientos(request):
    query = request.GET.get("q", "").strip()
    tipo = request.GET.get("tipo")
    fecha_filtro = request.GET.get("fecha_filtro", "").strip()
    movimientos = MovimientoInventario.objects.all().order_by("-fecha")
    error_fecha = None

    if query:
        movimientos = movimientos.filter(
            Q(producto__codigo__icontains=query) |
            Q(producto__nombre__icontains=query) |
            Q(comentario__icontains=query)
        )

    if tipo in ["entrada", "salida"]:
        movimientos = movimientos.filter(tipo=tipo)

    if fecha_filtro:
        # Normaliza separadores: convierte . y / a -
        fecha_filtro = fecha_filtro.replace(" ", "").replace("/", "-").replace(".", "-")
        try:
            # Rango tipo: 1-6-2025-15-6-2025
            if re.match(r"^\d{1,2}-\d{1,2}-\d{4}-\d{1,2}-\d{1,2}-\d{4}$", fecha_filtro):
                partes = fecha_filtro.split("-")
                inicio_str = f"{partes[0]}-{partes[1]}-{partes[2]}"
                fin_str = f"{partes[3]}-{partes[4]}-{partes[5]}"
                fecha_inicio = datetime.strptime(inicio_str, "%d-%m-%Y").date()
                fecha_fin = datetime.strptime(fin_str, "%d-%m-%Y").date()
                movimientos = movimientos.filter(fecha__date__gte=fecha_inicio, fecha__date__lte=fecha_fin)

            elif re.match(r"^>=\d{1,2}-\d{1,2}-\d{4}$", fecha_filtro):
                fecha = datetime.strptime(fecha_filtro[2:], "%d-%m-%Y").date()
                movimientos = movimientos.filter(fecha__date__gte=fecha)

            elif re.match(r"^<=\d{1,2}-\d{1,2}-\d{4}$", fecha_filtro):
                fecha = datetime.strptime(fecha_filtro[2:], "%d-%m-%Y").date()
                movimientos = movimientos.filter(fecha__date__lte=fecha)

            elif re.match(r"^>\d{1,2}-\d{1,2}-\d{4}$", fecha_filtro):
                fecha = datetime.strptime(fecha_filtro[1:], "%d-%m-%Y").date()
                movimientos = movimientos.filter(fecha__date__gt=fecha)

            elif re.match(r"^<\d{1,2}-\d{1,2}-\d{4}$", fecha_filtro):
                fecha = datetime.strptime(fecha_filtro[1:], "%d-%m-%Y").date()
                movimientos = movimientos.filter(fecha__date__lt=fecha)

            elif re.match(r"^=\d{1,2}-\d{1,2}-\d{4}$", fecha_filtro):
                fecha = datetime.strptime(fecha_filtro[1:], "%d-%m-%Y").date()
                movimientos = movimientos.filter(fecha__date=fecha)

            elif re.match(r"^\d{1,2}-\d{1,2}-\d{4}$", fecha_filtro):  # Fecha exacta sin =
                fecha = datetime.strptime(fecha_filtro, "%d-%m-%Y").date()
                movimientos = movimientos.filter(fecha__date=fecha)

            else:
                error_fecha = "Formato de fecha no válido. Usa uno como: 01-05-2024, <=01-05-2024, 01-05-2024-10-05-2024"

        except ValueError:
                error_fecha = "Fecha mal formada, usa el formato día-mes-año"

    return movimientos, error_fecha


def filtrar_productos(request):
    query = request.GET.get("q", "").strip()
    ubicacion = request.GET.get("ubicacion", "").strip()
    cantidad_filtro = request.GET.get("cantidad_filtro", "").strip()
    estado_activo = request.GET.get("estado_activo", "")
    alerta = request.GET.get("alerta", "")

    productos = Producto.objects.all().order_by("codigo")

    if query:
        productos = productos.filter(Q(nombre__icontains=query) | Q(codigo__icontains=query))

    if ubicacion == 'sin_ubicacion':
        productos = productos.filter(ubicacion__isnull=True)
    elif ubicacion:
        productos = productos.filter(ubicacion__nombre__icontains=ubicacion)

    if cantidad_filtro:
        cantidad_filtro = cantidad_filtro.replace(" ", "")
        try:
            if re.match(r"^\d+-\d+$", cantidad_filtro):
                inicio, fin = map(int, cantidad_filtro.split("-"))
                productos = productos.filter(cantidad__gte=inicio, cantidad__lte=fin)
            elif re.match(r"^<=\d+$", cantidad_filtro):
                productos = productos.filter(cantidad__lte=int(cantidad_filtro[2:]))
            elif re.match(r"^>=\d+$", cantidad_filtro):
                productos = productos.filter(cantidad__gte=int(cantidad_filtro[2:]))
            elif re.match(r"^<\d+$", cantidad_filtro):
                productos = productos.filter(cantidad__lt=int(cantidad_filtro[1:]))
            elif re.match(r"^>\d+$", cantidad_filtro):
                productos = productos.filter(cantidad__gt=int(cantidad_filtro[1:]))
            elif re.match(r"^=\d+$", cantidad_filtro):
                productos = productos.filter(cantidad=int(cantidad_filtro[1:]))
            elif re.match(r"^\d+$", cantidad_filtro):
                productos = productos.filter(cantidad=int(cantidad_filtro))
        except ValueError:
            pass

    if estado_activo == "activos":
        productos = productos.filter(activo=True)
    elif estado_activo == "inactivos":
        productos = productos.filter(activo=False)

    if alerta == "activa":
        productos = productos.filter(alerta_activa=True)
    elif alerta == "sin_alerta":
        productos = productos.filter(alerta_activa=False)

    return productos


@login_required
def exportar_productos_excel(request):
    productos = filtrar_productos(request)

    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet("Productos")

    bold = workbook.add_format({'bold': True})

    headers = ["Código", "Nombre", "Cantidad", "Ubicación", "Estado", "Alerta"]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, bold)

    for row, p in enumerate(productos, start=1):
        worksheet.write(row, 0, p.codigo)
        worksheet.write(row, 1, p.nombre)
        worksheet.write(row, 2, p.cantidad)
        worksheet.write(row, 3, p.ubicacion.nombre if p.ubicacion else "Sin ubicación")
        worksheet.write(row, 4, "Activo" if p.activo else "Inactivo")
        worksheet.write(row, 5, "Activa" if p.alerta_activa else "Sin alerta")

    workbook.close()
    output.seek(0)

    response = HttpResponse(output.read(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="productos.xlsx"'
    return response


@login_required
def exportar_productos_pdf(request):
    productos = filtrar_productos(request)

    template = get_template("productos/pdf_productos.html")
    html = template.render({"productos": productos})
    output = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=output)

    if pisa_status.err:
        return HttpResponse("Error al generar PDF", status=500)

    response = HttpResponse(output.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="productos.pdf"'
    return response
