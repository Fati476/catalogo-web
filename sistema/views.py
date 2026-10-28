from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
import requests

from .forms import RegistroForm
from .models import DetalleSolicitud, Favorito, Producto, Perfil

from .forms_producto import ProductoForm
from .models import Producto

from .forms_categoria import CategoriaForm
from .models import Categoria

from .forms_imagen import ProductoImagenForm
from .models import ProductoImagen

from .models import RegistroActividad


from .models import ProductoImagen

from django.contrib import messages

from django.db.models import Count, Max, Sum

from django.contrib.auth.models import User

from .models import SolicitudCotizacion

from django.http import JsonResponse

from django.contrib.admin.views.decorators import staff_member_required

from django.shortcuts import get_object_or_404, render

import json

from .models import Perfil

from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.conf import settings
import os

from .models import MedicionIoT
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

from .utils import enviar_correo


from datetime import timedelta
from django.db.models.functions import TruncMonth
from .models import (
    Producto,
    Categoria,
    SolicitudCotizacion,
    DetalleSolicitud,
)


from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

from reportlab.lib.pagesizes import landscape

from xml.sax.saxutils import escape

from django.db.models import Q


from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from .forms import CustomSetPasswordForm
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from .email_utils import enviar_correo_recuperacion
from google import genai
from google.genai import types


from .email_utils import (
    enviar_correo_cambio,
    enviar_correo_reversion,
)

@login_required
def inicio(request):

    productos_destacados = Producto.objects.filter(
        estado=True
    ).order_by('-id')[:6]

    categorias_destacadas = Categoria.objects.annotate(
        total_productos=Count('producto')
    ).order_by('-total_productos')[:3]

    favoritos_ids = Favorito.objects.filter(
        usuario=request.user
    ).values_list(
        'producto_id',
        flat=True
    )

    return render(
        request,
        'sistema/inicio.html',
        {
            'productos_destacados': productos_destacados,
            'categorias_destacadas': categorias_destacadas,
            'favoritos_ids': favoritos_ids
        }
    )


from .email_utils import enviar_bienvenida

def registro(request):

    if request.method == 'POST':

        form = RegistroForm(request.POST)

        if form.is_valid():

            usuario = form.save(commit=False)

            usuario.username = form.cleaned_data['email']
            usuario.email = form.cleaned_data['email']
            usuario.first_name = form.cleaned_data['first_name']
            usuario.last_name = form.cleaned_data['last_name']

            usuario.save()

            municipio = request.POST.get('municipio')
            estado = request.POST.get('estado')
            telefono = request.POST.get('telefono')

            Perfil.objects.create(
                usuario=usuario,
                municipio=municipio,
                estado=estado,
                telefono=telefono
            )

            grupo = Group.objects.get(name='Cliente')
            usuario.groups.add(grupo)


            # Correo de bienvenida
            enviar_bienvenida(usuario)

            # Mensaje para mostrar en login
            messages.success(
                request,
                "¡Registro exitoso! Ya puedes iniciar sesión con tu correo electrónico."
            )

            return redirect('login')

    else:

        form = RegistroForm()

    return render(request, 'registration/registro.html', {
        'form': form
    })


@login_required
def redireccion_inicio(request):

    if request.user.groups.filter(name='Administrador').exists():

        return redirect('panel_admin')

    elif request.user.groups.filter(name='Cliente').exists():

        return redirect('inicio')

    else:

        return redirect('login')


@login_required
def panel_admin(request):

    total_productos = Producto.objects.count()
    total_categorias = Categoria.objects.count()
    total_solicitudes = SolicitudCotizacion.objects.count()
    total_usuarios = User.objects.count()

    return render(request, 'admin/panel_admin.html', {
        'total_productos': total_productos,
        'total_categorias': total_categorias,
        'total_solicitudes': total_solicitudes,
        'total_usuarios': total_usuarios,
    })



from django.db.models import Q

from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.utils import timezone



@login_required
def seguridad_admin(request):

    # Verificar permisos de administrador
    if not request.user.groups.filter(name='Administrador').exists():
        raise PermissionDenied

    # Obtener los registros de actividad
    registros = RegistroActividad.objects.select_related(
        'usuario'
    ).all()

    # Obtener los filtros del formulario
    busqueda = request.GET.get('buscar', '').strip()
    tipo = request.GET.get('tipo', 'todos')
    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()

    fecha_inicio_valida = True
    fecha_fin_valida = True

    # Búsqueda por usuario, acción o descripción
    if busqueda:
        if busqueda.lower() in [
            'no identificado',
            'no identificada'
        ]:
            registros = registros.filter(
                usuario__isnull=True
            )
        else:
            registros = registros.filter(
                Q(usuario__username__icontains=busqueda)
                | Q(accion__icontains=busqueda)
                | Q(descripcion__icontains=busqueda)
            )

    # Filtro por tipo de actividad
    if tipo == 'correcto':
        registros = registros.filter(
            accion='Inicio de sesión'
        )
    elif tipo == 'fallido':
        registros = registros.filter(
            accion='Inicio de sesión fallido'
        )
    else:
        tipo = 'todos'

    # Filtro por fecha inicial
    if fecha_inicio:
        try:
            fecha_inicio_obj = datetime.strptime(
                fecha_inicio, '%Y-%m-%d'
            ).date()

            inicio = datetime.combine(
                fecha_inicio_obj,
                datetime.min.time()
            )

            if timezone.is_aware(timezone.now()):
                inicio = timezone.make_aware(
                    inicio,
                    timezone.get_current_timezone()
                )

            registros = registros.filter(
                fecha__gte=inicio
            )

        except ValueError:
            fecha_inicio = ''
            fecha_inicio_valida = False

    # Filtro por fecha final: incluye todo el día
    if fecha_fin:
        try:
            fecha_fin_obj = datetime.strptime(
                fecha_fin, '%Y-%m-%d'
            ).date()

            dia_siguiente = fecha_fin_obj + timedelta(days=1)

            fin_exclusivo = datetime.combine(
                dia_siguiente,
                datetime.min.time()
            )

            if timezone.is_aware(timezone.now()):
                fin_exclusivo = timezone.make_aware(
                    fin_exclusivo,
                    timezone.get_current_timezone()
                )

            registros = registros.filter(
                fecha__lt=fin_exclusivo
            )

        except ValueError:
            fecha_fin = ''
            fecha_fin_valida = False

    # Ordenar del más reciente al más antiguo
    registros = registros.order_by('-fecha')

    # Paginación: 10 registros por página
    paginador = Paginator(registros, 10)
    pagina = paginador.get_page(request.GET.get('page'))

    # Indicadores generales, sin aplicar los filtros
    total_accesos = RegistroActividad.objects.filter(
        accion='Inicio de sesión'
    ).count()

    intentos_fallidos = RegistroActividad.objects.filter(
        accion='Inicio de sesión fallido'
    ).count()

    total_actividades = RegistroActividad.objects.count()

    Usuario = get_user_model()
    total_usuarios = Usuario.objects.count()

    return render(request, 'admin/seguridad.html', {
        'registros': pagina,
        'pagina': pagina,
        'busqueda': busqueda,
        'tipo': tipo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'fecha_inicio_valida': fecha_inicio_valida,
        'fecha_fin_valida': fecha_fin_valida,
        'total_accesos': total_accesos,
        'intentos_fallidos': intentos_fallidos,
        'total_actividades': total_actividades,
        'total_usuarios': total_usuarios,
    })



def obtener_registros_para_exportar(request):
    from datetime import datetime, timedelta
    from django.core.exceptions import PermissionDenied
    from django.utils import timezone

    if not request.user.groups.filter(
        name='Administrador'
    ).exists():
        raise PermissionDenied

    registros = RegistroActividad.objects.select_related(
        'usuario'
    ).all()

    busqueda = request.GET.get('buscar', '').strip()
    tipo = request.GET.get('tipo', 'todos')
    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()

    if busqueda:
        if busqueda.lower() in ['no identificado', 'no identificada']:
            registros = registros.filter(usuario__isnull=True)
        else:
            registros = registros.filter(
                Q(usuario__username__icontains=busqueda)
                | Q(accion__icontains=busqueda)
                | Q(descripcion__icontains=busqueda)
            )

    if tipo == 'correcto':
        registros = registros.filter(accion='Inicio de sesión')
    elif tipo == 'fallido':
        registros = registros.filter(
            accion='Inicio de sesión fallido'
        )

    if fecha_inicio:
        try:
            fecha = datetime.strptime(
                fecha_inicio, '%Y-%m-%d'
            ).date()
            inicio = datetime.combine(fecha, datetime.min.time())

            if timezone.is_aware(timezone.now()):
                inicio = timezone.make_aware(
                    inicio, timezone.get_current_timezone()
                )

            registros = registros.filter(fecha__gte=inicio)
        except ValueError:
            pass

    if fecha_fin:
        try:
            fecha = datetime.strptime(
                fecha_fin, '%Y-%m-%d'
            ).date()
            fin = datetime.combine(
                fecha + timedelta(days=1), datetime.min.time()
            )

            if timezone.is_aware(timezone.now()):
                fin = timezone.make_aware(
                    fin, timezone.get_current_timezone()
                )

            registros = registros.filter(fecha__lt=fin)
        except ValueError:
            pass

    return registros.order_by('-fecha')


@login_required
def exportar_seguridad_excel(request):
    registros = obtener_registros_para_exportar(request)

    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Historial de seguridad'

    hoja.append([
        'Usuario', 'Tipo de actividad', 'Descripción', 'Fecha y hora'
    ])

    for celda in hoja[1]:
        celda.font = Font(bold=True, color='FFFFFF')
        celda.fill = PatternFill(
            fill_type='solid', fgColor='172554'
        )
        celda.alignment = Alignment(
            horizontal='center', vertical='center'
        )

    for registro in registros:
        fecha = registro.fecha

        if fecha and fecha.tzinfo:
            from django.utils import timezone
            fecha = timezone.localtime(fecha).replace(tzinfo=None)

        hoja.append([
            registro.usuario.username if registro.usuario else 'No identificado',
            registro.accion,
            registro.descripcion,
            fecha,
        ])

    hoja.freeze_panes = 'A2'
    hoja.auto_filter.ref = hoja.dimensions

    for columna, ancho in {
        'A': 22, 'B': 28, 'C': 65, 'D': 22
    }.items():
        hoja.column_dimensions[columna].width = ancho

    for fila in hoja.iter_rows(min_row=2):
        for celda in fila:
            celda.alignment = Alignment(
                vertical='top', wrap_text=True
            )

    for celda in hoja['D'][1:]:
        celda.number_format = 'dd/mm/yyyy hh:mm:ss'

    salida = BytesIO()
    libro.save(salida)
    salida.seek(0)

    respuesta = HttpResponse(
        salida.getvalue(),
        content_type=(
            'application/vnd.openxmlformats-officedocument.'
            'spreadsheetml.sheet'
        )
    )
    respuesta['Content-Disposition'] = (
        'attachment; filename="historial_seguridad.xlsx"'
    )
    return respuesta



@login_required
def exportar_seguridad_pdf(request):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from django.conf import settings
    from django.utils import timezone
    import os
    from xml.sax.saxutils import escape

    registros = obtener_registros_para_exportar(request)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        'attachment; filename="historial_seguridad.pdf"'
    )

    pdf = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    logo_path = os.path.join(
        settings.BASE_DIR,
        "static",
        "img",
        "logo_cooperativa.png"
    )

    # ENCABEZADO Y LOGO
    if os.path.exists(logo_path):
        pdf.drawImage(
            logo_path,
            30,
            height - 100,
            width=90,
            height=90,
            mask="auto",
            preserveAspectRatio=True
        )

    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawCentredString(
        width / 2 + 40,
        height - 45,
        "Comercializadora Cooperativa de Sustancias Químicas"
    )
    pdf.drawCentredString(
        width / 2 + 40,
        height - 65,
        "para uso del Artesano Pirotécnico, S.A. de C.V."
    )

    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(
        width / 2 + 40,
        height - 82,
        "Venta de Sustancias Químicas para la Pirotecnia"
    )
    pdf.drawCentredString(
        width / 2 + 40,
        height - 95,
        "Venta de Artificios Pirotécnicos y Transporte Especializado"
    )

    pdf.setStrokeColor(colors.HexColor("#C9A227"))
    pdf.setLineWidth(2)
    pdf.line(30, height - 105, width - 30, height - 105)

    # TÍTULO
    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(
        width / 2,
        height - 145,
        "HISTORIAL DE SEGURIDAD"
    )

    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        40,
        height - 175,
        f"Fecha de exportación: "
        f"{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}"
    )

    pdf.drawString(
        40,
        height - 192,
        f"Total de registros: {registros.count()}"
    )

    # TABLA
    margen_izquierdo = 30
    margen_derecho = width - 30
    ancho_tabla = margen_derecho - margen_izquierdo

    x_usuario = 38
    x_accion = 145
    x_descripcion = 270
    x_fecha = 500

    ancho_usuario = 100
    ancho_accion = 120
    ancho_descripcion = 220
    ancho_fecha = 75

    alto_fila = 30
    y = height - 230

    def dibujar_encabezado(y_actual):
        pdf.setFillColor(colors.HexColor("#F3F4F6"))
        pdf.rect(
            margen_izquierdo,
            y_actual - alto_fila + 5,
            ancho_tabla,
            alto_fila,
            fill=1,
            stroke=0
        )

        pdf.setFillColorRGB(0, 0, 0)
        pdf.setFont("Helvetica-Bold", 8)

        pdf.drawString(x_usuario, y_actual - 12, "Usuario")
        pdf.drawString(x_accion, y_actual - 12, "Actividad")
        pdf.drawString(x_descripcion, y_actual - 12, "Descripción")
        pdf.drawString(x_fecha, y_actual - 12, "Fecha y hora")

        pdf.setStrokeColor(colors.HexColor("#C9A227"))
        pdf.setLineWidth(1)
        pdf.line(
            margen_izquierdo,
            y_actual - alto_fila + 5,
            margen_derecho,
            y_actual - alto_fila + 5
        )

    def ajustar_texto(texto, max_caracteres):
        texto = str(texto or "")
        palabras = texto.split()
        lineas = []
        linea = ""

        for palabra in palabras:
            if len(linea) + len(palabra) + 1 > max_caracteres:
                if linea:
                    lineas.append(linea)
                linea = palabra
            else:
                linea = f"{linea} {palabra}".strip()

        if linea:
            lineas.append(linea)

        return lineas or [""]

    dibujar_encabezado(y)
    y -= alto_fila

    for registro in registros:
        usuario = (
            registro.usuario.username
            if registro.usuario
            else "No identificado"
        )

        fecha = registro.fecha
        if fecha and timezone.is_aware(fecha):
            fecha = timezone.localtime(fecha)

        fecha_texto = (
            fecha.strftime("%d/%m/%Y %H:%M")
            if fecha else ""
        )

        columnas = [
            (x_usuario, ajustar_texto(usuario, 16)),
            (x_accion, ajustar_texto(registro.accion, 18)),
            (x_descripcion, ajustar_texto(registro.descripcion, 34)),
            (x_fecha, ajustar_texto(fecha_texto, 13)),
        ]

        max_lineas = max(len(lineas) for _, lineas in columnas)
        alto_real = max(24, max_lineas * 10 + 10)

        # Crear una página nueva cuando no haya espacio suficiente.
        if y - alto_real < 85:
            pdf.setStrokeColor(colors.HexColor("#C9A227"))
            pdf.line(30, 65, width - 30, 65)

            pdf.setFont("Helvetica", 8)
            pdf.drawString(
                30,
                48,
                "San Mateo Tlalchichilpan, Almoloya de Juárez, Edo. de México"
            )
            pdf.drawString(30, 34, "C.P. 50900")
            pdf.drawRightString(width - 30, 48, "Tel. 725 136 07 31")
            pdf.drawRightString(
                width - 30, 34, "comer_coop_2013@live.com.mx"
            )

            pdf.showPage()

            # Repetir el encabezado institucional en cada página.
            if os.path.exists(logo_path):
                pdf.drawImage(
                    logo_path,
                    30,
                    height - 100,
                    width=90,
                    height=90,
                    mask="auto",
                    preserveAspectRatio=True
                )

            pdf.setFont("Helvetica-Bold", 15)
            pdf.drawCentredString(
                width / 2 + 40,
                height - 45,
                "Comercializadora Cooperativa de Sustancias Químicas"
            )
            pdf.drawCentredString(
                width / 2 + 40,
                height - 65,
                "para uso del Artesano Pirotécnico, S.A. de C.V."
            )

            pdf.setFont("Helvetica", 9)
            pdf.drawCentredString(
                width / 2 + 40,
                height - 82,
                "Venta de Sustancias Químicas para la Pirotecnia"
            )
            pdf.drawCentredString(
                width / 2 + 40,
                height - 95,
                "Venta de Artificios Pirotécnicos y Transporte Especializado"
            )

            pdf.setStrokeColor(colors.HexColor("#C9A227"))
            pdf.setLineWidth(2)
            pdf.line(30, height - 105, width - 30, height - 105)

            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawCentredString(
                width / 2,
                height - 145,
                "HISTORIAL DE SEGURIDAD"
            )

            y = height - 190
            dibujar_encabezado(y)
            y -= alto_fila

        # Filas alternadas en blanco y gris claro.
        if registros.count() and (registro.id % 2 == 0):
            pdf.setFillColor(colors.HexColor("#F9FAFB"))
            pdf.rect(
                margen_izquierdo,
                y - alto_real + 5,
                ancho_tabla,
                alto_real,
                fill=1,
                stroke=0
            )

        pdf.setFillColorRGB(0, 0, 0)
        pdf.setFont("Helvetica", 7)

        for x, lineas in columnas:
            for indice, linea in enumerate(lineas):
                pdf.drawString(
                    x,
                    y - 10 - (indice * 10),
                    linea[:100]
                )

        pdf.setStrokeColor(colors.HexColor("#E5E7EB"))
        pdf.setLineWidth(0.5)
        pdf.line(
            margen_izquierdo,
            y - alto_real + 5,
            margen_derecho,
            y - alto_real + 5
        )

        y -= alto_real

    # PIE DE PÁGINA
    pdf.setStrokeColor(colors.HexColor("#C9A227"))
    pdf.setLineWidth(1)
    pdf.line(30, 65, width - 30, 65)

    pdf.setFont("Helvetica", 8)
    pdf.drawString(
        30,
        48,
        "San Mateo Tlalchichilpan, Almoloya de Juárez, Edo. de México"
    )
    pdf.drawString(30, 34, "C.P. 50900")
    pdf.drawRightString(width - 30, 48, "Tel. 725 136 07 31")
    pdf.drawRightString(
        width - 30,
        34,
        "comer_coop_2013@live.com.mx"
    )

    pdf.save()
    return response




from django.core.paginator import Paginator

@login_required
def lista_productos(request):

    productos = Producto.objects.all().order_by('-id')

    # agregar primera imagen
    for producto in productos:
        producto.imagen_principal = producto.imagenes.first()

    paginator = Paginator(productos, 12)

    page = request.GET.get('page')
    productos = paginator.get_page(page)

    categorias = Categoria.objects.all()

    return render(
        request,
        'admin/productos/lista.html',
        {
            'productos': productos,
            'categorias': categorias
        }
    )



@login_required
def agregar_producto(request):

    if request.method == 'POST':

        form = ProductoForm(request.POST)

        if form.is_valid():

            producto = form.save()

            imagenes = request.FILES.getlist('imagen')

            for imagen in imagenes:

                ProductoImagen.objects.create(
                    producto=producto,
                    imagen=imagen
                )

            return redirect('lista_productos')

    else:

        form = ProductoForm()

    return render(
        request,
        'admin/productos/agregar.html',
        {
            'form': form
        }
    )



@login_required
def editar_producto(request, id):

    producto = Producto.objects.get(id=id)

    if request.method == 'POST':

        form = ProductoForm(
            request.POST,
            instance=producto
        )

        if form.is_valid():

            producto = form.save(commit=False)
            producto.estado = True
            producto.save()

            imagenes = request.FILES.getlist('imagen')

            for imagen in imagenes:
                ProductoImagen.objects.create(
                    producto=producto,
                    imagen=imagen
                )

            return redirect('lista_productos')

        else:
            print("ERRORES DEL FORM:", form.errors)

    else:
        form = ProductoForm(instance=producto)

    imagenes = ProductoImagen.objects.filter(producto=producto)

    return render(request, 'admin/productos/editar.html', {
        'form': form,
        'producto': producto,
        'imagenes': imagenes
    })


@login_required
def eliminar_imagen(request, id):

    imagen = ProductoImagen.objects.get(id=id)
    producto_id = imagen.producto.id

    imagen.delete()

    return redirect('editar_producto', id=producto_id)


@login_required
def eliminar_producto(request, id):

    producto = Producto.objects.get(id=id)

    producto.delete()

    return redirect('lista_productos')

@login_required
def lista_categorias(request):

    categorias_lista = Categoria.objects.annotate(
        total_productos=Count('producto')
    ).order_by('nombre')

    paginator = Paginator(categorias_lista, 12)

    page_number = request.GET.get('page')

    categorias = paginator.get_page(page_number)

    return render(
        request,
        'admin/categorias/lista.html',
        {
            'categorias': categorias
        }
    )


@login_required
def agregar_categoria(request):

    if request.method == 'POST':

        form = CategoriaForm(request.POST, request.FILES)

        if form.is_valid():

            categoria = form.save()

            messages.success(
                request,
                f'Categoría "{categoria.nombre}" creada correctamente.'
            )

            return redirect('lista_categorias')

    else:
        form = CategoriaForm()

    return render(
        request,
        'admin/categorias/agregar.html',
        {
            'form': form
        }
    )


@login_required
def editar_categoria(request, id):

    categoria = Categoria.objects.get(id=id)

    if request.method == 'POST':

        form = CategoriaForm(
            request.POST,
            request.FILES,
            instance=categoria
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Categoría actualizada correctamente.'
            )

            return redirect('lista_categorias')

    else:

        form = CategoriaForm(instance=categoria)

    return render(
        request,
        'admin/categorias/editar.html',
        {
            'form': form,
            'categoria': categoria
        }
    )


@login_required
def eliminar_categoria(request, id):

    categoria = Categoria.objects.get(id=id)

    if categoria.producto_set.exists():

        messages.error(
            request,
            f'No puedes eliminar la categoría "{categoria.nombre}" porque tiene productos asociados.'
        )

        return redirect('lista_categorias')

    nombre = categoria.nombre

    categoria.delete()

    messages.success(
        request,
        f'La categoría "{nombre}" fue eliminada correctamente.'
    )

    return redirect('lista_categorias')





@login_required
def dashboard(request):
    if not request.user.groups.filter(name="Administrador").exists():
        raise PermissionDenied

    hoy = timezone.localdate()
    inicio_semana = hoy - timedelta(days=hoy.weekday())

    # Filtros de fechas y estado
    fecha_inicio = request.GET.get(
        "fecha_inicio", inicio_semana.isoformat()
    )
    fecha_fin = request.GET.get(
        "fecha_fin", hoy.isoformat()
    )
    estado = request.GET.get("estado", "todos")

    # Validar fechas
    try:
        desde = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        hasta = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

        if desde > hasta:
            raise ValueError

    except (ValueError, TypeError):
        desde = inicio_semana
        hasta = hoy
        fecha_inicio = desde.isoformat()
        fecha_fin = hasta.isoformat()

    # Solicitudes enviadas dentro del periodo seleccionado
    solicitudes = SolicitudCotizacion.objects.filter(
        enviada=True,
        fecha__date__gte=desde,
        fecha__date__lte=hasta,
    )

    if estado in ("revision", "cotizada", "rechazada"):
        solicitudes = solicitudes.filter(estado=estado)
    else:
        estado = "todos"

    # Indicadores generales
    total_productos = Producto.objects.count()
    total_categorias = Categoria.objects.count()
    productos_activos = Producto.objects.filter(estado=True).count()
    productos_inactivos = Producto.objects.filter(estado=False).count()
    total_usuarios = User.objects.count()

    ultimos_productos = Producto.objects.order_by("-id")[:5]

    total_solicitudes = solicitudes.count()
    solicitudes_revision = solicitudes.filter(
        estado="revision"
    ).count()
    solicitudes_cotizadas = solicitudes.filter(
        estado="cotizada"
    ).count()
    solicitudes_rechazadas = solicitudes.filter(
        estado="rechazada"
    ).count()

    # Gráfica de solicitudes por estado
    grafica_estados = {
        "labels": ["En revisión", "Cotizadas", "Rechazadas"],
        "valores": [
            solicitudes_revision,
            solicitudes_cotizadas,
            solicitudes_rechazadas,
        ],
    }

    # Gráfica mensual: últimos seis meses, incluido el actual
    primer_dia_mes = hoy.replace(day=1)
    meses = []

    cursor = primer_dia_mes

    for _ in range(6):
        meses.append(cursor)

        if cursor.month == 1:
            cursor = cursor.replace(
                year=cursor.year - 1,
                month=12,
            )
        else:
            cursor = cursor.replace(month=cursor.month - 1)

    meses.reverse()

    nombres_meses = [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
    ]

    etiquetas_meses = []
    valores_meses = []

    for mes in meses:
        if mes.month == 12:
            siguiente_mes = mes.replace(
                year=mes.year + 1,
                month=1,
            )
        else:
            siguiente_mes = mes.replace(
                month=mes.month + 1,
            )

        # Límites en la zona horaria local para contar
        # las fechas que corresponden a cada mes local.
        inicio_periodo = timezone.make_aware(
            datetime.combine(mes, datetime.min.time())
        )
        fin_periodo = timezone.make_aware(
            datetime.combine(
                siguiente_mes,
                datetime.min.time(),
            )
        )

        cantidad = SolicitudCotizacion.objects.filter(
            enviada=True,
            fecha__gte=inicio_periodo,
            fecha__lt=fin_periodo,
        ).count()

        etiquetas_meses.append(
            f"{nombres_meses[mes.month - 1]} {mes.year}"
        )
        valores_meses.append(cantidad)

    grafica_meses = {
        "labels": etiquetas_meses,
        "valores": valores_meses,
    }

    # Gráfica de productos por categoría
    productos_categoria = (
        Categoria.objects
        .annotate(total=Count("producto"))
        .order_by("-total")[:8]
    )

    grafica_categorias = {
        "labels": [
            categoria.nombre
            for categoria in productos_categoria
        ],
        "valores": [
            categoria.total
            for categoria in productos_categoria
        ],
    }

    # Productos más cotizados de todo el historial
    productos_mas_cotizados = list(
        DetalleSolicitud.objects
        .filter(
            solicitud__enviada=True,
            seleccionado=True,
        )
        .values("producto_id", "producto__nombre")
        .annotate(
            total_solicitudes=Count(
                "solicitud_id",
                distinct=True,
            ),
            total_unidades=Sum("cantidad"),
        )
        .order_by(
            "-total_solicitudes",
            "-total_unidades",
        )[:5]
    )

    grafica_productos = {
        "labels": [
            producto["producto__nombre"]
            for producto in productos_mas_cotizados
        ],
        "solicitudes": [
            producto["total_solicitudes"]
            for producto in productos_mas_cotizados
        ],
        "unidades": [
            producto["total_unidades"] or 0
            for producto in productos_mas_cotizados
        ],
    }

    # Datos enviados al HTML
    contexto = {
        "total_productos": total_productos,
        "total_categorias": total_categorias,
        "productos_activos": productos_activos,
        "productos_inactivos": productos_inactivos,
        "total_usuarios": total_usuarios,
        "ultimos_productos": ultimos_productos,

        "total_solicitudes": total_solicitudes,
        "solicitudes_revision": solicitudes_revision,
        "solicitudes_cotizadas": solicitudes_cotizadas,
        "solicitudes_rechazadas": solicitudes_rechazadas,

        "productos_mas_cotizados": productos_mas_cotizados,

        "grafica_estados_json": grafica_estados,
        "grafica_meses_json": grafica_meses,
        "grafica_categorias_json": grafica_categorias,
        "grafica_productos_json": grafica_productos,

        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "estado_seleccionado": estado,
    }

    return render(
        request,
        "admin/dashboard/dashboard.html",
        contexto,
    )





@login_required
def lista_usuarios(request):

    usuarios_lista = User.objects.select_related(
        'perfil'
    ).order_by('-date_joined')

    paginator = Paginator(
        usuarios_lista,
        10
    )

    page_number = request.GET.get('page')

    usuarios = paginator.get_page(page_number)

    return render(
        request,
        'admin/usuarios/lista.html',
        {
            'usuarios': usuarios
        }
    )

@login_required
def cambiar_estado_usuario(request, id):

    usuario = User.objects.get(id=id)

    usuario.is_active = not usuario.is_active

    usuario.save()

    if usuario.is_active:

        messages.success(
            request,
            f'El usuario "{usuario.username}" fue activado.'
        )

    else:

        messages.success(
            request,
            f'El usuario "{usuario.username}" fue desactivado.'
        )

    return redirect('lista_usuarios')


@login_required
def lista_solicitudes(request):

    solicitudes = SolicitudCotizacion.objects.filter(
        enviada=True
    ).order_by("-fecha")

    pendientes = solicitudes.filter(
        estado="revision"
    ).count()

    cotizadas = solicitudes.filter(
        estado="cotizada"
    ).count()

    rechazadas = solicitudes.filter(
        estado="rechazada"
    ).count()

    paginator = Paginator(
        solicitudes,
        10   # 10 solicitudes por página
    )

    page_number = request.GET.get("page")

    solicitudes = paginator.get_page(page_number)

    abrir_modal = request.session.pop(
        "abrir_modal",
        None
    )

    return render(
        request,
        "admin/solicitudes/lista.html",
        {
            "solicitudes": solicitudes,
            "pendientes": pendientes,
            "cotizadas": cotizadas,
            "rechazadas": rechazadas,
            "abrir_modal": abrir_modal,
        },
    )


#Clientes 

@login_required
def productos_por_categoria(request, id):

    categoria = Categoria.objects.get(id=id)

    productos_lista = Producto.objects.filter(
        categoria=categoria,
        estado=True
    ).order_by('-id')

    for producto in productos_lista:
        producto.imagen_principal = producto.imagenes.first()

    paginator = Paginator(productos_lista, 8)

    page_number = request.GET.get('page')

    productos = paginator.get_page(page_number)

    favoritos_ids = []

    if request.user.is_authenticated:
        favoritos_ids = Favorito.objects.filter(
            usuario=request.user
        ).values_list(
            'producto_id',
            flat=True
        )

    return render(
        request,
        'sistema/productos_categoria.html',
        {
            'categoria': categoria,
            'productos': productos,
            'favoritos_ids': favoritos_ids,
            'total_productos': productos_lista.count()
        }
    )


@login_required
def toggle_favorito(request, producto_id):

    producto = Producto.objects.get(id=producto_id)

    favorito = Favorito.objects.filter(
        usuario=request.user,
        producto=producto
    )

    if favorito.exists():
        favorito.delete()
        estado = "eliminado"
    else:
        Favorito.objects.create(
            usuario=request.user,
            producto=producto
        )
        estado = "agregado"

    return JsonResponse({
        "estado": estado,
        "producto_id": producto_id
    })

@login_required
def agregar_cotizacion(request, producto_id):

    producto = get_object_or_404(
        Producto,
        id=producto_id
    )

    solicitud_id = request.session.get("solicitud_editando_id")

    solicitud = None

    if solicitud_id:
        solicitud = SolicitudCotizacion.objects.filter(
            id=solicitud_id,
            usuario=request.user,
            enviada=False
        ).first()

    if solicitud is None:
        solicitud = SolicitudCotizacion.objects.filter(
            usuario=request.user,
            enviada=False
        ).order_by("-id").first()

    if solicitud is None:
        solicitud = SolicitudCotizacion.objects.create(
            usuario=request.user,
            enviada=False,
            estado="revision"
        )

    detalle, creado = DetalleSolicitud.objects.get_or_create(
        solicitud=solicitud,
        producto=producto,
        defaults={
            "cantidad": 1,
            "seleccionado": True
        }
    )

    if not creado:
        detalle.cantidad += 1
        detalle.seleccionado = True
        detalle.save()

    return redirect("solicitudes")

def todas_categorias(request):
    categorias = Categoria.objects.all().order_by('nombre')

    return render(request, 'sistema/todas_categorias.html', {
        'categorias': categorias
    })




def todos_productos(request):

    productos_lista = Producto.objects.filter(
        estado=True
    ).order_by('-id')

    # Asignar la primera imagen a cada producto
    for producto in productos_lista:
        producto.imagen_principal = producto.imagenes.first()

    total_productos = productos_lista.count()

    paginator = Paginator(productos_lista, 12)

    page = request.GET.get('page')

    productos = paginator.get_page(page)

    favoritos_ids = Favorito.objects.filter(
        usuario=request.user
    ).values_list(
        'producto_id',
        flat=True
    ) if request.user.is_authenticated else []

    return render(
        request,
        'sistema/todos_productos.html',
        {
            'productos': productos,
            'total_productos': total_productos,
            'favoritos_ids': favoritos_ids
        }
    )


@login_required
def favoritos(request):

    favoritos_ids = Favorito.objects.filter(
        usuario=request.user
    ).values_list(
        'producto_id',
        flat=True
    )

    productos_lista = Producto.objects.filter(
        id__in=favoritos_ids,
        estado=True
    ).order_by('-id')

    for producto in productos_lista:
        producto.imagen_principal = producto.imagenes.first()

    paginator = Paginator(productos_lista, 12)

    page = request.GET.get('page')

    productos = paginator.get_page(page)

    return render(
        request,
        'sistema/favoritos.html',
        {
            'productos': productos,
            'favoritos_ids': favoritos_ids
        }
    )


@login_required
def solicitudes(request):

    solicitud_id = (
        request.session.get("piroia_solicitud_id")
        or request.session.get("solicitud_editando_id")
    )

    solicitud = None
    editando = False
    piroia_activa = False

    if solicitud_id:
        solicitud = SolicitudCotizacion.objects.filter(
            id=solicitud_id,
            usuario=request.user,
            enviada=False,
            estado="revision"
        ).first()

        if solicitud:
            editando = bool(
                request.session.get("solicitud_editando_id")
            )
            piroia_activa = bool(
                request.session.get("piroia_solicitud_id")
            )
        else:
            request.session.pop("solicitud_editando_id", None)
            request.session.pop("piroia_solicitud_id", None)

    if solicitud is None:
        solicitud = SolicitudCotizacion.objects.filter(
            usuario=request.user,
            enviada=False
        ).order_by("-id").first()

    if solicitud and not solicitud.detalles.exists():

        if not editando:
            solicitud.delete()
            solicitud = None

    total_productos = 0
    total_unidades = 0

    if solicitud:
        total_productos = solicitud.detalles.count()
        total_unidades = sum(
            detalle.cantidad
            for detalle in solicitud.detalles.all()
        )

    numero_usuario = None

    if solicitud and editando:
        numero_usuario = solicitud.numero_usuario

    return render(
        request,
        "sistema/solicitudes.html",
        {
            "solicitud": solicitud,
            "total_productos": total_productos,
            "total_unidades": total_unidades,
            "editando": editando,
            "piroia_activa": piroia_activa,
            "numero_usuario": numero_usuario,
        }
    )

@login_required
def eliminar_detalle(request, id):

    detalle = DetalleSolicitud.objects.get(
        id=id,
        solicitud__usuario=request.user
    )

    detalle.delete()

    return JsonResponse({
        'ok': True
    })


@login_required
def aumentar_cantidad(request, id):

    detalle = DetalleSolicitud.objects.get(
        id=id,
        solicitud__usuario=request.user
    )

    detalle.cantidad += 1
    detalle.save()

    return JsonResponse({
        'cantidad': detalle.cantidad
    })


@login_required
def disminuir_cantidad(request, id):

    detalle = DetalleSolicitud.objects.get(
        id=id,
        solicitud__usuario=request.user
    )

    if detalle.cantidad > 1:
        detalle.cantidad -= 1
        detalle.save()

    return JsonResponse({
        'cantidad': detalle.cantidad
    })

import logging

@login_required
def enviar_solicitud(request):
    solicitud_id = request.session.get("solicitud_editando_id")
    solicitud = None

    if solicitud_id:
        solicitud = SolicitudCotizacion.objects.filter(
            id=solicitud_id,
            usuario=request.user,
            enviada=False,
            estado="revision"
        ).first()

    if solicitud is None:
        solicitud = SolicitudCotizacion.objects.filter(
            usuario=request.user,
            enviada=False
        ).order_by("-id").first()

    if solicitud is None:
        return JsonResponse({
            "ok": False,
            "mensaje": "No existe una solicitud activa."
        }, status=400)

    detalles_seleccionados = solicitud.detalles.filter(
        seleccionado=True
    )

    if not detalles_seleccionados.exists():
        return JsonResponse({
            "ok": False,
            "mensaje": "Debes seleccionar al menos un producto."
        }, status=400)

    detalles_no_seleccionados = solicitud.detalles.filter(
        seleccionado=False
    )

    numero_usuario = solicitud.numero_usuario

    if numero_usuario is None:
        ultimo_numero = SolicitudCotizacion.objects.filter(
            usuario=request.user,
            numero_usuario__isnull=False
        ).aggregate(
            maximo=Max("numero_usuario")
        )["maximo"] or 0

        numero_usuario = ultimo_numero + 1

    if detalles_no_seleccionados.exists():
        nueva_solicitud = SolicitudCotizacion.objects.create(
            usuario=request.user,
            enviada=True,
            estado="revision",
            bloqueada=False,
            numero_usuario=numero_usuario
        )

        for detalle in detalles_seleccionados:
            DetalleSolicitud.objects.create(
                solicitud=nueva_solicitud,
                producto=detalle.producto,
                cantidad=detalle.cantidad,
                seleccionado=True
            )

        detalles_seleccionados.delete()

    else:
        solicitud.enviada = True
        solicitud.estado = "revision"
        solicitud.bloqueada = False
        solicitud.numero_usuario = numero_usuario

        solicitud.save(update_fields=[
            "enviada",
            "estado",
            "bloqueada",
            "numero_usuario"
        ])

        nueva_solicitud = solicitud

    # Enviar correo al administrador sin impedir el envío
    # de la solicitud si ocurre un error con el correo.
    try:
        notificar_nueva_solicitud(nueva_solicitud)
    except Exception:
        logging.exception(
            "Error al enviar la notificación por correo "
            "de la solicitud #%s",
            nueva_solicitud.id
        )

    request.session.pop("solicitud_editando_id", None)
    request.session.pop("piroia_solicitud_id", None)

    messages.success(
        request,
        "Tu solicitud fue enviada correctamente. "
        "Puedes consultar su estado aquí."
    )

    return JsonResponse({
        "ok": True,
        "mensaje": "Solicitud enviada correctamente.",
        "solicitud_id": nueva_solicitud.id,
        "numero_usuario": nueva_solicitud.numero_usuario,
        "redirect_url": reverse("mis_cotizaciones")
    })

@login_required
def mis_cotizaciones(request):

    solicitudes = (
        SolicitudCotizacion.objects
        .filter(
            usuario=request.user,
            enviada=True
        )
        .order_by("-fecha")
    )

    total_cotizaciones = solicitudes.count()

    total_revision = solicitudes.filter(
        estado="revision"
    ).count()

    total_cotizadas = solicitudes.filter(
        estado="cotizada"
    ).count()

    total_rechazadas = solicitudes.filter(
        estado="rechazada"
    ).count()

    return render(
        request,
        "sistema/mis_cotizaciones.html",
        {
            "solicitudes": solicitudes,
            "total_cotizaciones": total_cotizaciones,
            "total_revision": total_revision,
            "total_cotizadas": total_cotizadas,
            "total_rechazadas": total_rechazadas,
        }
    )


@login_required
def administrar_cotizaciones(request):
    solicitudes = (
        SolicitudCotizacion.objects
        .filter(enviada=True)
        .order_by("-fecha")
    )

    return render(
        request,
        "sistema/administrar_cotizaciones.html",
        {
            "solicitudes": solicitudes
        }
    )

from decimal import Decimal, InvalidOperation

from .email_utils import enviar_cotizacion, enviar_correo_rechazo
from django.db.models import Max

@login_required
def generar_cotizacion(request, id):

    solicitud = get_object_or_404(
        SolicitudCotizacion,
        id=id,
        enviada=True,
        estado="revision"
    )

    if request.method != "POST":

        return redirect(
            "detalle_solicitud_admin",
            id=solicitud.id
        )

    if solicitud.numero_usuario is None:

        messages.error(
            request,
            "La solicitud no tiene un número asignado."
        )

        return redirect(
            "detalle_solicitud_admin",
            id=solicitud.id
        )

    for detalle in solicitud.detalles.all():

        disponibilidad = request.POST.get(
            f"disponibilidad_{detalle.id}"
        )

        precio = request.POST.get(
            f"precio_{detalle.id}",
            ""
        ).strip()

        observacion = request.POST.get(
            f"observacion_{detalle.id}",
            ""
        ).strip()

        disponibilidades_validas = [
            "disponible",
            "bajo_pedido",
            "no_disponible",
            "descontinuado",
        ]

        if disponibilidad not in disponibilidades_validas:

            messages.error(
                request,
                f"Selecciona una disponibilidad válida para "
                f"'{detalle.producto.nombre}'."
            )

            return redirect(
                "detalle_solicitud_admin",
                id=solicitud.id
            )

        # Disponible: requiere precio, no requiere observación.
        if disponibilidad == "disponible":

            if not precio:

                messages.error(
                    request,
                    f"Debes asignar un precio al producto "
                    f"'{detalle.producto.nombre}'."
                )

                return redirect(
                    "detalle_solicitud_admin",
                    id=solicitud.id
                )

            try:

                precio_decimal = Decimal(precio)

                if precio_decimal <= 0:
                    raise InvalidOperation

            except (InvalidOperation, ValueError):

                messages.error(
                    request,
                    f"El precio de '{detalle.producto.nombre}' "
                    f"es inválido."
                )

                return redirect(
                    "detalle_solicitud_admin",
                    id=solicitud.id
                )

            detalle.precio_aplicado = precio_decimal
            detalle.observacion_disponibilidad = None

        # Bajo pedido: requiere precio y observación.
        elif disponibilidad == "bajo_pedido":

            if not precio:

                messages.error(
                    request,
                    f"Debes asignar un precio al producto bajo pedido "
                    f"'{detalle.producto.nombre}'."
                )

                return redirect(
                    "detalle_solicitud_admin",
                    id=solicitud.id
                )

            if not observacion:

                messages.error(
                    request,
                    f"Debes indicar el tiempo o las condiciones de entrega "
                    f"de '{detalle.producto.nombre}'."
                )

                return redirect(
                    "detalle_solicitud_admin",
                    id=solicitud.id
                )

            try:

                precio_decimal = Decimal(precio)

                if precio_decimal <= 0:
                    raise InvalidOperation

            except (InvalidOperation, ValueError):

                messages.error(
                    request,
                    f"El precio de '{detalle.producto.nombre}' "
                    f"es inválido."
                )

                return redirect(
                    "detalle_solicitud_admin",
                    id=solicitud.id
                )

            detalle.precio_aplicado = precio_decimal
            detalle.observacion_disponibilidad = observacion

        # No disponible o descontinuado:
        # no requiere precio, pero sí una justificación.
        else:

            if not observacion:

                messages.error(
                    request,
                    f"Debes justificar por qué "
                    f"'{detalle.producto.nombre}' no puede cotizarse."
                )

                return redirect(
                    "detalle_solicitud_admin",
                    id=solicitud.id
                )

            detalle.precio_aplicado = None
            detalle.observacion_disponibilidad = observacion

        detalle.disponibilidad = disponibilidad

        detalle.save(
            update_fields=[
                "disponibilidad",
                "precio_aplicado",
                "observacion_disponibilidad",
            ]
        )

    solicitud.estado = "cotizada"
    solicitud.bloqueada = True

    solicitud.save(
        update_fields=[
            "estado",
            "bloqueada"
        ]
    )

    try:

        pdf_response = descargar_cotizacion_pdf(
            request,
            solicitud.id
        )

        pdf_bytes = pdf_response.content

        enviar_cotizacion(
            solicitud.usuario.email,
            pdf_bytes,
            solicitud.numero_usuario
        )

        messages.success(
            request,
            "La cotización fue generada y enviada correctamente al cliente."
        )

    except Exception as e:

        print("Error enviando correo:", e)

        messages.warning(
            request,
            "La cotización se generó correctamente, "
            "pero ocurrió un problema al enviar el correo."
        )

    return redirect("lista_solicitudes")
    


@login_required
def rechazar_cotizacion(request, id):

    solicitud = get_object_or_404(
        SolicitudCotizacion,
        id=id,
        enviada=True,
        estado="revision"
    )

    if solicitud.numero_usuario is None:

        messages.error(
            request,
            "La solicitud no tiene un número asignado."
        )

        return redirect(
            "detalle_solicitud_admin",
            id=solicitud.id
        )

    solicitud.estado = "rechazada"
    solicitud.bloqueada = True

    solicitud.save(
        update_fields=[
            "estado",
            "bloqueada"
        ]
    )

    try:

        enviar_correo_rechazo(
            solicitud.usuario.email,
            solicitud.numero_usuario
        )

        messages.success(
            request,
            "La solicitud fue rechazada y el cliente fue notificado por correo."
        )

    except Exception as e:

        print("Error enviando correo:", e)

        messages.warning(
            request,
            "La solicitud fue rechazada, pero no se pudo enviar el correo."
        )

    return redirect("lista_solicitudes")




@login_required
def descargar_cotizacion_pdf(request, id):

    solicitud = get_object_or_404(
        SolicitudCotizacion,
        id=id
    )

    if solicitud.numero_usuario is None:

        messages.error(
            request,
            "La cotización no tiene un folio asignado."
        )

        return redirect("lista_solicitudes")

    folio_interno = f"COT-{solicitud.id:04d}"
    numero_cliente = solicitud.numero_usuario

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{folio_interno}.pdf"'
    )

    pdf = canvas.Canvas(
        response,
        pagesize=letter
    )

    width, height = letter

    # ==========================
    # LOGO
    # ==========================

    logo_path = os.path.join(
        settings.BASE_DIR,
        "static",
        "img",
        "logo_cooperativa.png"
    )

    if os.path.exists(logo_path):

        pdf.drawImage(
            logo_path,
            30,
            height - 100,
            width=90,
            height=90,
            mask="auto",
            preserveAspectRatio=True
        )

    # ==========================
    # ENCABEZADO
    # ==========================

    pdf.setFont(
        "Helvetica-Bold",
        17
    )

    pdf.drawCentredString(
        width / 2 + 40,
        height - 45,
        "Comercializadora Cooperativa de Sustancias Químicas"
    )

    pdf.drawCentredString(
        width / 2 + 40,
        height - 65,
        "para uso del Artesano Pirotécnico, S.A. de C.V."
    )

    pdf.setFont(
        "Helvetica",
        10
    )

    pdf.drawCentredString(
        width / 2 + 40,
        height - 82,
        "Venta de Sustancias Químicas para la Pirotecnia,"
    )

    pdf.drawCentredString(
        width / 2 + 40,
        height - 95,
        "Venta de Artificios Pirotécnicos y Transporte Especializado"
    )

    pdf.setStrokeColor(
        colors.HexColor("#C9A227")
    )

    pdf.setLineWidth(2)

    pdf.line(
        30,
        height - 105,
        width - 30,
        height - 105
    )

    # ==========================
    # TÍTULO
    # ==========================

    pdf.setFillColorRGB(
        0,
        0,
        0
    )

    pdf.setFont(
        "Helvetica-Bold",
        18
    )

    pdf.drawCentredString(
        width / 2,
        height - 145,
        "COTIZACIÓN"
    )

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        40,
        height - 175,
        f"Folio interno: {folio_interno}"
    )

    pdf.drawString(
        330,
        height - 175,
        f"Cotización No. {numero_cliente}"
    )

    nombre = (
        solicitud.usuario.get_full_name()
        or solicitud.usuario.email
    )

    pdf.drawString(
        40,
        height - 195,
        f"Cliente: {nombre}"
    )

    pdf.drawString(
        40,
        height - 215,
        f"Fecha: {solicitud.fecha.strftime('%d/%m/%Y')}"
    )

    # ==========================
    # TABLA
    # ==========================

    y = height - 255

    pdf.setFillColor(
        colors.HexColor("#F3F4F6")
    )

    pdf.rect(
        35,
        y,
        540,
        22,
        fill=1
    )

    pdf.setFillColorRGB(
        0,
        0,
        0
    )

    pdf.setFont(
        "Helvetica-Bold",
        9
    )

    pdf.drawString(
        45,
        y + 7,
        "Producto"
    )

    pdf.drawString(
        260,
        y + 7,
        "Cantidad"
    )

    pdf.drawString(
        325,
        y + 7,
        "Disponibilidad"
    )

    pdf.drawString(
        445,
        y + 7,
        "Precio"
    )

    pdf.drawString(
        510,
        y + 7,
        "Subtotal"
    )

    y -= 20

    total = 0

    pdf.setFont(
        "Helvetica",
        9
    )

    for detalle in solicitud.detalles.all():

        disponibilidad_texto = (
            detalle.get_disponibilidad_display()
        )

        precio = float(
            detalle.precio_aplicado or 0
        )

        if detalle.disponibilidad in [
            "disponible",
            "bajo_pedido"
        ]:

            subtotal = precio * detalle.cantidad

            total += subtotal

            precio_texto = f"${precio:,.2f}"
            subtotal_texto = f"${subtotal:,.2f}"

        else:

            precio_texto = "N/A"
            subtotal_texto = "$0.00"

        pdf.setFillColorRGB(
            0,
            0,
            0
        )

        pdf.setFont(
            "Helvetica",
            9
        )

        pdf.drawString(
            45,
            y,
            detalle.producto.nombre[:30]
        )

        pdf.drawString(
            280,
            y,
            str(detalle.cantidad)
        )

        pdf.drawString(
            325,
            y,
            disponibilidad_texto[:19]
        )

        pdf.drawString(
            445,
            y,
            precio_texto
        )

        pdf.drawString(
            510,
            y,
            subtotal_texto
        )

        y -= 16

        if detalle.observacion_disponibilidad:

            pdf.setFillColor(
                colors.HexColor("#6B7280")
            )

            pdf.setFont(
                "Helvetica-Oblique",
                8
            )

            observacion = (
                detalle.observacion_disponibilidad[:85]
            )

            pdf.drawString(
                55,
                y,
                f"Observación: {observacion}"
            )

            y -= 16

        y -= 4

    # ==========================
    # TOTAL
    # ==========================

    y -= 10

    pdf.setStrokeColor(
        colors.HexColor("#C9A227")
    )

    pdf.line(
        390,
        y + 15,
        560,
        y + 15
    )

    pdf.setFillColorRGB(
        0,
        0,
        0
    )

    pdf.setFont(
        "Helvetica-Bold",
        15
    )

    pdf.drawRightString(
        560,
        y,
        f"TOTAL: ${total:,.2f}"
    )

    # ==========================
    # OBSERVACIONES GENERALES
    # ==========================

    y -= 45

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(
        40,
        y,
        "Observaciones generales"
    )

    y -= 20

    pdf.setFont(
        "Helvetica",
        10
    )

    pdf.drawString(
        40,
        y,
        "• Los productos no disponibles no se incluyen en el total."
    )

    y -= 18

    pdf.drawString(
        40,
        y,
        "• Los productos bajo pedido están sujetos a las condiciones indicadas."
    )

    y -= 18

    pdf.drawString(
        40,
        y,
        "• Cotización válida por 15 días naturales."
    )

    y -= 18

    pdf.drawString(
        40,
        y,
        "• Precios sujetos a cambios sin previo aviso."
    )

    y -= 18

    pdf.drawString(
        40,
        y,
        "• Gracias por confiar en Cooperativa Pirotécnica."
    )

    # ==========================
    # PIE
    # ==========================

    pdf.setStrokeColor(
        colors.HexColor("#C9A227")
    )

    pdf.line(
        30,
        65,
        width - 30,
        65
    )

    pdf.setFont(
        "Helvetica",
        8
    )

    pdf.drawString(
        30,
        48,
        "San Mateo Tlalchichilpan, Almoloya de Juárez, Edo. de México"
    )

    pdf.drawString(
        30,
        34,
        "C.P. 50900"
    )

    pdf.drawRightString(
        width - 30,
        48,
        "Tel. 725 136 07 31"
    )

    pdf.drawRightString(
        width - 30,
        34,
        "comer_coop_2013@live.com.mx"
    )

    pdf.save()

    return response


@login_required
def descargar_preorden_pdf(request):
    # Obtener la solicitud activa de PiroIA o la que se está editando.
    solicitud_id = (
        request.session.get("piroia_solicitud_id")
        or request.session.get("solicitud_editando_id")
    )

    if not solicitud_id:
        return HttpResponse(
            "No tienes una preorden activa para descargar.",
            status=404
        )

    # Solo se permite descargar la preorden propia y sin cotizar.
    solicitud = get_object_or_404(
        SolicitudCotizacion,
        id=solicitud_id,
        usuario=request.user,
        enviada=False,
        estado="revision",
        bloqueada=False,
    )

    detalles = list(
        solicitud.detalles.select_related("producto").all()
    )

    if not detalles:
        return HttpResponse(
            "La preorden no contiene productos.",
            status=400
        )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="PRE-{solicitud.id:04d}.pdf"'
    )

    pdf = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Encabezado
    pdf.setFillColor(colors.HexColor("#101C35"))
    pdf.rect(0, height - 125, width, 125, fill=1, stroke=0)

    pdf.setFillColor(colors.HexColor("#E2C875"))
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(width / 2, height - 38, "CATÁLOGO WEB")

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(width / 2, height - 70, "PREORDEN")

    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(
        width / 2,
        height - 94,
        "DOCUMENTO INFORMATIVO - NO ES UNA COTIZACIÓN"
    )

    # Datos del usuario y solicitud
    y = height - 160
    nombre = (
        request.user.get_full_name()
        or request.user.username
    )

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, y, f"Folio de preorden: PRE-{solicitud.id:04d}")
    y -= 20
    pdf.drawString(40, y, f"Usuario: {nombre[:70]}")
    y -= 20
    pdf.drawString(
        40,
        y,
        f"Fecha: {solicitud.fecha.strftime('%d/%m/%Y')}"
    )
    y -= 35

    # Tabla de productos
    def dibujar_encabezado_tabla(pos_y):
        pdf.setFillColor(colors.HexColor("#F3F4F6"))
        pdf.rect(35, pos_y - 5, 540, 24, fill=1, stroke=0)

        pdf.setFillColor(colors.HexColor("#101C35"))
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(45, pos_y + 3, "Producto")
        pdf.drawRightString(555, pos_y + 3, "Cantidad")

    dibujar_encabezado_tabla(y)
    y -= 28

    for detalle in detalles:
        if y < 100:
            pdf.showPage()
            y = height - 60
            dibujar_encabezado_tabla(y)
            y -= 28

        nombre_producto = detalle.producto.nombre
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(45, y, nombre_producto[:75])
        pdf.drawRightString(555, y, str(detalle.cantidad))

        pdf.setStrokeColor(colors.HexColor("#E5E7EB"))
        pdf.line(40, y - 8, 570, y - 8)
        y -= 24

    # Aviso final
    if y < 100:
        pdf.showPage()
        y = height - 60

    y -= 10
    pdf.setFillColor(colors.HexColor("#8A6415"))
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(40, y, "IMPORTANTE")

    y -= 18
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(
        40,
        y,
        "Este documento es evidencia de los productos solicitados."
    )
    y -= 15
    pdf.drawString(
        40,
        y,
        "No contiene precios oficiales ni confirma disponibilidad."
    )
    y -= 15
    pdf.drawString(
        40,
        y,
        "La cotización deberá ser elaborada y confirmada por el personal."
    )

    pdf.save()
    return response


@login_required
def detalle_producto(request, id):

    producto = get_object_or_404(
        Producto,
        id=id
    )

    producto.imagen_principal = producto.imagenes.first()

    favoritos_ids = Favorito.objects.filter(
        usuario=request.user
    ).values_list(
        'producto_id',
        flat=True
    )

    return render(
        request,
        'sistema/detalle_producto.html',
        {
            'producto': producto,
            'favoritos_ids': favoritos_ids
        }
    )


@login_required
@require_POST
def actualizar_seleccion_detalle(request, id):

    detalle = get_object_or_404(
        DetalleSolicitud,
        id=id,
        solicitud__usuario=request.user,
        solicitud__enviada=False
    )

    data = json.loads(request.body)

    detalle.seleccionado = data.get("seleccionado", True)
    detalle.save()

    return JsonResponse({
        "ok": True,
        "seleccionado": detalle.seleccionado
    })


@login_required
def editar_solicitud_en_revision(request, id):

    solicitud = get_object_or_404(
        SolicitudCotizacion,
        id=id,
        usuario=request.user
    )

    if solicitud.estado != "revision":

        messages.error(
            request,
            "Esta solicitud ya fue procesada y no puede editarse."
        )

        return redirect("mis_cotizaciones")

    if solicitud.bloqueada:

        messages.error(
            request,
            "No puedes editar esta solicitud porque un administrador ya la está revisando."
        )

        return redirect("mis_cotizaciones")

    if not solicitud.enviada:

        messages.warning(
            request,
            "Esta solicitud ya se encuentra en edición."
        )

        return redirect("solicitudes")

    if solicitud.numero_usuario is None:

        ultimo_numero = SolicitudCotizacion.objects.filter(
            usuario=request.user,
            numero_usuario__isnull=False
        ).aggregate(
            maximo=Max("numero_usuario")
        )["maximo"] or 0

        solicitud.numero_usuario = ultimo_numero + 1

    solicitud.enviada = False

    solicitud.save(
        update_fields=[
            "enviada",
            "numero_usuario"
        ]
    )

    request.session["solicitud_editando_id"] = solicitud.id

    # Esta es una solicitud existente, no un borrador nuevo de PiroIA.
    request.session["piroia_creando_solicitud"] = False

    return redirect("solicitudes")

@login_required
def eliminar_solicitud_en_revision(request, id):

    solicitud = get_object_or_404(
        SolicitudCotizacion,
        id=id,
        usuario=request.user
    )

    if solicitud.estado != "revision":

        messages.error(
            request,
            "Esta solicitud ya fue procesada y no puede eliminarse."
        )

        return redirect("mis_cotizaciones")

    if solicitud.bloqueada:

        messages.error(
            request,
            "No puedes eliminar esta solicitud porque un administrador ya la está revisando."
        )

        return redirect("mis_cotizaciones")

    if not solicitud.enviada:

        messages.warning(
            request,
            "No puedes eliminarla desde aquí porque actualmente está en edición."
        )

        return redirect("solicitudes")

    solicitud.delete()

    messages.success(
        request,
        "La solicitud fue eliminada correctamente."
    )

    return redirect("mis_cotizaciones")

@login_required
def cancelar_edicion_solicitud(request, id):

    solicitud = get_object_or_404(
        SolicitudCotizacion,
        id=id,
        usuario=request.user,
        enviada=False,
        estado="revision"
    )

    # ----------------------------------------------------------
    # BORRADOR NUEVO CREADO POR PIROIA
    # ----------------------------------------------------------

    es_nueva_piroia = request.session.get(
        "piroia_creando_solicitud",
        False
    )

    if es_nueva_piroia and request.session.get(
        "piroia_solicitud_id"
    ) == solicitud.id:

        solicitud.delete()

        request.session.pop(
            "piroia_solicitud_id",
            None
        )

        request.session.pop(
            "solicitud_editando_id",
            None
        )

        request.session.pop(
            "piroia_creando_solicitud",
            None
        )

        messages.info(
            request,
            "La solicitud creada por PiroIA fue cancelada."
        )

        return redirect("solicitudes")

    # ----------------------------------------------------------
    # EDICIÓN DE UNA SOLICITUD YA EXISTENTE
    # ----------------------------------------------------------

    solicitud.enviada = True
    solicitud.bloqueada = False

    solicitud.save(
        update_fields=[
            "enviada",
            "bloqueada"
        ]
    )

    request.session.pop(
        "solicitud_editando_id",
        None
    )

    request.session.pop(
        "piroia_solicitud_id",
        None
    )

    request.session.pop(
        "piroia_creando_solicitud",
        None
    )

    messages.info(
        request,
        "La edición fue cancelada. La solicitud volvió a quedar en revisión."
    )

    return redirect("mis_cotizaciones")


@login_required
def perfil(request):

    perfil, creado = Perfil.objects.get_or_create(
        usuario=request.user
    )

    total_favoritos = Favorito.objects.filter(
        usuario=request.user
    ).count()

    total_solicitudes = SolicitudCotizacion.objects.filter(
        usuario=request.user,
        enviada=True
    ).count()

    total_cotizaciones = SolicitudCotizacion.objects.filter(
        usuario=request.user,
        estado="cotizada"
    ).count()

    if request.method == "POST":

        nuevo_correo = request.POST.get(
            "email",
            ""
        ).strip().lower()

        correo_anterior = request.user.email.strip().lower()

        # Verificar que el correo no pertenezca a otro usuario
        correo_existente = User.objects.filter(
            username__iexact=nuevo_correo
        ).exclude(
            id=request.user.id
        ).exists()

        if correo_existente:

            messages.error(
                request,
                "Ese correo electrónico ya está registrado."
            )

            return redirect("perfil")

        # Actualizar datos del usuario
        request.user.first_name = request.POST.get(
            "first_name",
            ""
        ).strip()

        request.user.last_name = request.POST.get(
            "last_name",
            ""
        ).strip()

        request.user.email = nuevo_correo
        request.user.username = nuevo_correo

        request.user.save()

        # Registrar el cambio solamente si el correo cambió
        if correo_anterior != nuevo_correo:

            # Cancelar cualquier cambio pendiente anterior
            CambioCorreo.objects.filter(
                usuario=request.user,
                usado=False,
                revertido=False,
                cancelado=False
            ).update(
                cancelado=True
            )

            # Crear el nuevo cambio pendiente
            cambio = CambioCorreo.objects.create(
                usuario=request.user,
                correo_anterior=correo_anterior,
                correo_nuevo=nuevo_correo
            )

            # Generar un token seguro
            token = signing.dumps(
                {
                    "cambio_id": cambio.id
                },
                salt="cambio-correo"
            )

            # Construir la URL de reversión
            url_reversion = request.build_absolute_uri(
                reverse(
                    "revertir_cambio_correo",
                    kwargs={
                        "token": token
                    }
                )
            )

            try:
                # Avisar al correo nuevo
                enviar_correo_cambio(
                    nuevo_correo
                )

                # Enviar el enlace al correo anterior
                enviar_correo_reversion(
                    correo_anterior,
                    url_reversion
                )

            except Exception as error:
                print(
                    "Error al enviar correos por cambio de correo:",
                    error
                )

                messages.warning(
                    request,
                    "El correo fue actualizado, pero no fue posible enviar las notificaciones por correo electrónico."
                )

        # Actualizar datos del perfil
        perfil.telefono = request.POST.get(
            "telefono",
            ""
        ).strip()

        perfil.estado = request.POST.get(
            "estado",
            ""
        ).strip()

        perfil.municipio = request.POST.get(
            "municipio",
            ""
        ).strip()

        if request.FILES.get("foto"):
            perfil.foto = request.FILES.get("foto")

        perfil.save()

        messages.success(
            request,
            "Perfil actualizado correctamente. Si cambiaste tu correo, utiliza el nuevo para iniciar sesión."
        )

        return redirect("perfil")

    return render(
        request,
        "sistema/perfil.html",
        {
            "perfil": perfil,
            "total_favoritos": total_favoritos,
            "total_solicitudes": total_solicitudes,
            "total_cotizaciones": total_cotizaciones,
        }
    )

def password_reset_custom(request):

    if request.method == "POST":
        email = request.POST.get("email")

        usuario = User.objects.filter(
            email__iexact=email,
            is_active=True
        ).first()

        if usuario:
            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            token = default_token_generator.make_token(usuario)

            reset_url = request.build_absolute_uri(
                reverse(
                    "password_reset_confirm",
                    kwargs={
                        "uidb64": uid,
                        "token": token
                    }
                )
            )

            enviar_correo_recuperacion(usuario, reset_url)

        return redirect("password_reset_done")

    return render(request, "registration/password_reset_form.html")


def password_reset_done_custom(request):

    return render(request, "registration/password_reset_done.html")


def password_reset_confirm_custom(request, uidb64, token):

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        usuario = User.objects.get(pk=uid)

    except Exception:
        usuario = None

    if usuario is not None and default_token_generator.check_token(usuario, token):

        if request.method == "POST":

            form = CustomSetPasswordForm(usuario, request.POST)

            if form.is_valid():
                form.save()
                return redirect("password_reset_complete")

        else:
            form = CustomSetPasswordForm(usuario)

        return render(request, "registration/password_reset_confirm.html", {
            "form": form,
            "validlink": True
        })

    return render(request, "registration/password_reset_confirm.html", {
        "validlink": False
    })


def password_reset_complete_custom(request):

    return render(request, "registration/password_reset_complete.html")


@login_required
def detalle_solicitud_admin(request, id):

    solicitud = get_object_or_404(
        SolicitudCotizacion,
        id=id
    )

    if not solicitud.enviada:

        messages.warning(
            request,
            "Esta solicitud está siendo modificada por el cliente. "
            "Podrás revisarla cuando vuelva a enviarla."
        )

        return redirect("lista_solicitudes")

    if solicitud.estado == "revision":

        solicitud.bloqueada = True

        solicitud.save(
            update_fields=["bloqueada"]
        )

    return render(
        request,
        "admin/solicitudes/detalle.html",
        {
            "solicitud": solicitud
        }
    )


@login_required
def liberar_solicitud_admin(request, id):

    solicitud = get_object_or_404(
        SolicitudCotizacion,
        id=id
    )

    # Solo se libera si sigue en revisión.
    # Si ya fue cotizada o rechazada, permanece cerrada.
    if solicitud.estado == "revision":

        solicitud.bloqueada = False

        solicitud.save(
            update_fields=["bloqueada"]
        )

    messages.info(
        request,
        "La solicitud quedó disponible nuevamente."
    )

    return redirect("lista_solicitudes")
@login_required
def detalle_usuario(request, id):

    usuario = get_object_or_404(
        User,
        id=id
    )

    perfil = usuario.perfil

    solicitudes = SolicitudCotizacion.objects.filter(
        usuario=usuario
    ).order_by("-fecha")

    favoritos = Favorito.objects.filter(
        usuario=usuario
    ).count()

    context = {
        "usuario": usuario,
        "perfil": perfil,
        "solicitudes": solicitudes,
        "favoritos": favoritos,
        "total_solicitudes": solicitudes.count(),
        "cotizadas": solicitudes.filter(
            estado="cotizada"
        ).count(),
        "revision": solicitudes.filter(
            estado="revision"
        ).count(),
        "rechazadas": solicitudes.filter(
            estado="rechazada"
        ).count(),
    }

    return render(
        request,
        "admin/usuarios/detalle.html",
        context
    )




@login_required
def estado_cotizaciones_ajax(request):

    es_admin = (
        request.user.is_staff
        or request.user.groups.filter(
            name="Administrador"
        ).exists()
    )

    if es_admin:

        solicitudes = SolicitudCotizacion.objects.all().order_by("id")

    else:

        solicitudes = SolicitudCotizacion.objects.filter(
            usuario=request.user
        ).order_by("id")

    datos = list(
        solicitudes.values(
            "id",
            "enviada",
            "estado",
            "bloqueada",
            "numero_usuario"
        )
    )

    return JsonResponse({
        "ok": True,
        "solicitudes": datos
    })



@login_required
def estado_cotizaciones_ajax(request):

    es_admin = (
        request.user.is_staff
        or request.user.groups.filter(
            name="Administrador"
        ).exists()
    )

    if es_admin:
        solicitudes = SolicitudCotizacion.objects.all().order_by("id")
    else:
        solicitudes = SolicitudCotizacion.objects.filter(
            usuario=request.user
        ).order_by("id")

    datos = list(
        solicitudes.values(
            "id",
            "enviada",
            "estado",
            "bloqueada",
            "numero_usuario"
        )
    )

    return JsonResponse({
        "ok": True,
        "solicitudes": datos
    })



from django.core import signing
from django.contrib.auth import logout
from .models import CambioCorreo


def revertir_cambio_correo(request, token):

    try:
        datos = signing.loads(
            token,
            salt="cambio-correo",
            max_age=60 * 60 * 24
        )

    except signing.SignatureExpired:
        return render(
            request,
            "sistema/correo_reversion_resultado.html",
            {
                "estado": "expirado"
            }
        )

    except signing.BadSignature:
        return render(
            request,
            "sistema/correo_reversion_resultado.html",
            {
                "estado": "invalido"
            }
        )

    cambio_id = datos.get("cambio_id")

    try:
        cambio = CambioCorreo.objects.select_related(
            "usuario"
        ).get(
            id=cambio_id
        )

    except CambioCorreo.DoesNotExist:
        return render(
            request,
            "sistema/correo_reversion_resultado.html",
            {
                "estado": "invalido"
            }
        )

    if cambio.usado or cambio.revertido or cambio.cancelado:
        return render(
           request,
            "sistema/correo_reversion_resultado.html",
            {
                "estado": "usado",
                "cambio": cambio
            }
        )
    usuario = cambio.usuario

    # Evitar restaurar un correo que ahora pertenece a otra cuenta
    correo_ocupado = User.objects.filter(
        username__iexact=cambio.correo_anterior
    ).exclude(
        id=usuario.id
    ).exists()

    if correo_ocupado:
        return render(
            request,
            "sistema/correo_reversion_resultado.html",
            {
                "estado": "ocupado",
                "cambio": cambio
            }
        )

    usuario.email = cambio.correo_anterior
    usuario.username = cambio.correo_anterior
    usuario.save(
        update_fields=[
            "email",
            "username"
        ]
    )

    cambio.usado = True
    cambio.revertido = True
    cambio.save(
        update_fields=[
            "usado",
            "revertido"
        ]
    )

    # Si el usuario tenía una sesión iniciada, se cierra
    if request.user.is_authenticated and request.user.id == usuario.id:
        logout(request)

    return render(
        request,
        "sistema/correo_reversion_resultado.html",
        {
            "estado": "revertido",
            "cambio": cambio
        }
    )


@login_required

def chatbot_ia(request):

    """

    PiroIA:

    - Consulta el catálogo

    - Crea solicitudes de cotización

    - Modifica solicitudes mediante lenguaje natural

    - Edita solicitudes existentes

    - Cancela solicitudes

    - Prepara solicitudes para que el usuario las revise y envíe desde Solicitudes

    - Funciona con texto y voz desde el frontend

    """

    try:

        # ==========================================================

        # 0. DATOS RECIBIDOS DEL FRONTEND

        # ==========================================================

        data = json.loads(request.body)



        pregunta = (

            data.get("mensaje", "")

            .strip()

        )



        modo = (

            data.get("modo", "consulta")

            .strip()

            .lower()

        )



        pagina_actual = (

            data.get("pagina_actual", "")

            .strip()

        )



        en_solicitudes = (

            pagina_actual.rstrip("/") == "/solicitudes"

        )



        historial = data.get(

            "historial",

            []

        )

        if not isinstance(historial, list):

            historial = []

        # Conservamos solamente las últimas intervenciones.

        historial_reciente = historial[-12:]

        if not pregunta:

            return JsonResponse({

                "ok": False,

                "respuesta": (

                    "Escribe o di algo para que pueda ayudarte."

                )

            })

        # ==========================================================

        # 1. CATÁLOGO REAL

        # ==========================================================

        productos_catalogo = (

            Producto.objects

            .filter(

                estado=True

            )

            .select_related(

                "categoria"

            )

            .prefetch_related(

                "imagenes"

            )

        )

        catalogo = []

        for producto in productos_catalogo:

            imagen_url = ""

            try:

                primera_imagen = (

                    producto.imagenes.first()

                )

                if (

                    primera_imagen

                    and primera_imagen.imagen

                ):

                    imagen_url = (

                        primera_imagen.imagen.url

                    )

            except Exception:

                imagen_url = ""

            # IMPORTANTE:

            # El ID solamente se utiliza internamente.

            # NO se muestra al usuario.

            #

            # El precio NO se manda a la IA.

            catalogo.append({

                "id": producto.id,

                "nombre": producto.nombre,

                "descripcion": (

                    producto.descripcion

                    or ""

                ),

                "categoria": (

                    producto.categoria.nombre

                    if producto.categoria

                    else ""

                ),

                "imagen": imagen_url,

            })

        # ==========================================================

        # 2. CONSULTAS DIRECTAS SIN IA

        # ==========================================================

        pregunta_lower = pregunta.lower()

        palabras_precio = [

            "precio",

            "precios",

            "costo",

            "costos",

            "cuánto cuesta",

            "cuanto cuesta",

            "cuánto vale",

            "cuanto vale"

        ]

        # ----------------------------------------------------------

        # PRECIOS

        # ----------------------------------------------------------

        if any(

            palabra in pregunta_lower

            for palabra in palabras_precio

        ):

            return JsonResponse({

                "ok": True,

                "respuesta": (

                    "El precio de los productos se determina "

                    "mediante cotización. Si deseas, puedo ayudarte "

                    "a preparar una solicitud con la cantidad "

                    "que necesitas."

                ),

                "confirmado": False,

                "accion": "ninguna",

                "productos": []

            })

        # ----------------------------------------------------------

        # LISTA DE PRODUCTOS

        # ----------------------------------------------------------

        if modo != "solicitud":

            consulta_productos = any(

                frase in pregunta_lower

                for frase in [

                    "qué productos hay",

                    "que productos hay",

                    "qué productos tienen",

                    "que productos tienen",

                    "productos del catálogo",

                    "productos del catalogo",

                    "lista de productos",

                    "listar productos",

                    "qué tienen",

                    "que tienen",

                    "qué venden",

                    "que venden",

                    "muéstrame los productos",

                    "muestrame los productos"

                ]

            )

            if consulta_productos:

                nombres = [

                    producto.nombre

                    for producto in productos_catalogo

                ]

                if nombres:

                    respuesta_productos = (

                        "Estos son los productos "

                        "disponibles en el catálogo:\n\n"

                        +

                        "\n".join(

                            "• " + nombre

                            for nombre in nombres

                        )

                    )

                else:

                    respuesta_productos = (

                        "Actualmente no hay productos "

                        "disponibles en el catálogo."

                    )

                return JsonResponse({

                    "ok": True,

                    "respuesta": respuesta_productos,

                    "confirmado": False,

                    "accion": "ninguna",

                    "productos": []

                })

        # ----------------------------------------------------------

        # CATEGORÍAS

        # ----------------------------------------------------------

        if modo != "solicitud":

            consulta_categorias = any(

                frase in pregunta_lower

                for frase in [

                    "qué categorías hay",

                    "que categorias hay",

                    "categorías del catálogo",

                    "categorias del catalogo",

                    "lista de categorías",

                    "lista de categorias"

                ]

            )

            if consulta_categorias:

                categorias = sorted({

                    producto.categoria.nombre

                    for producto in productos_catalogo

                    if producto.categoria

                })

                if categorias:

                    respuesta_categorias = (

                        "Estas son las categorías disponibles:\n\n"

                        +

                        "\n".join(

                            "• " + categoria

                            for categoria in categorias

                        )

                    )

                else:

                    respuesta_categorias = (

                        "Actualmente no hay categorías disponibles."

                    )

                return JsonResponse({

                    "ok": True,

                    "respuesta": respuesta_categorias,

                    "confirmado": False,

                    "accion": "ninguna",

                    "productos": []

                })

        # ==========================================================

        # 3. OBTENER API KEY DE GROQ

        # ==========================================================

        api_key = os.getenv(

            "GROQ_API_KEY"

        )

        if not api_key:

            return JsonResponse({

                "ok": False,

                "respuesta": (

                    "No se encontró la configuración "

                    "de PiroIA."

                )

            }, status=500)

        # ==========================================================

        # 4. SOLICITUD ACTIVA

        # ==========================================================

        solicitud_id = (

            request.session.get(

                "piroia_solicitud_id"

            )

            or

            request.session.get(

                "solicitud_editando_id"

            )

        )

        solicitud_actual = None

        if solicitud_id:

            solicitud_actual = (

                SolicitudCotizacion.objects.filter(

                    id=solicitud_id,

                    usuario=request.user,

                    enviada=False,

                    estado="revision",

                    bloqueada=False

                ).first()

            )

            if solicitud_actual is None:

                request.session.pop(

                    "piroia_solicitud_id",

                    None

                )

                request.session.pop(

                    "solicitud_editando_id",

                    None

                )

                request.session.modified = True 

       
        frases_preorden_pdf = [
            "genera el pdf de mi preorden",
            "generar pdf de preorden",
            "descargar mi preorden",
            "genera mi preorden",
            "descarga la preorden",
            "generate my pre-order pdf",
            "generate a pre-order pdf",
            "download my pre-order",
            "download the pre-order",
            "create my pre-order pdf",
        ]

        quiere_pdf_preorden = any(
            frase in pregunta_lower
            for frase in frases_preorden_pdf
        )

        if quiere_pdf_preorden:
            if solicitud_actual is None:
                return JsonResponse({
                    "ok": False,
                    "respuesta": "No tienes una preorden activa para descargar."
                }, status=400)

            return JsonResponse({
                "ok": True,
                "respuesta": "Tu PDF de preorden está listo para descargar.",
                "descargar_pdf_url": reverse("descargar_preorden_pdf"),
                "confirmado": False,
                "accion": "ninguna",
                "productos": []
            })
       
        

        es_nueva_piroia = bool(
            request.session.get("piroia_creando_solicitud", False)
        )

        es_edicion_existente = bool(
            solicitud_actual
            and request.session.get("solicitud_editando_id") == solicitud_actual.id
            and not es_nueva_piroia
        )

        # ==========================================================

        # 5. PRODUCTOS DE LA SOLICITUD ACTIVA

        # ==========================================================

        productos_solicitud = []

        if solicitud_actual:

            detalles = (

                solicitud_actual.detalles

                .select_related(

                    "producto"

                )

                .all()

            )

            for detalle in detalles:

                productos_solicitud.append({

                    "id": detalle.producto.id,

                    "nombre": detalle.producto.nombre,

                    "cantidad": detalle.cantidad

                })

        # ==========================================================

        # 6. ACCIONES DIRECTAS

        # ==========================================================

        # ----------------------------------------------------------

        # EDITAR SOLICITUD EXISTENTE

        # ----------------------------------------------------------

        palabras_editar = [

            "editar mi solicitud",

            "editar la solicitud",

            "modificar mi solicitud",

            "modificar la solicitud",

            "abre mi solicitud",

            "abrir mi solicitud",

            "quiero editar la solicitud",

            "quiero modificar la solicitud"

        ]

        if (

            modo == "solicitud"

            and any(

                palabra in pregunta_lower

                for palabra in palabras_editar

            )

        ):

            import re

            numeros = re.findall(

                r"\b\d+\b",

                pregunta_lower

            )

            numero_solicitud = None

            if numeros:

                numero_solicitud = int(

                    numeros[-1]

                )

            if numero_solicitud is None:

                return JsonResponse({

                    "ok": True,

                    "respuesta": (

                        "Claro. Dime el número de la "

                        "solicitud que deseas editar."

                    ),

                    "confirmado": False,

                    "accion": "ninguna",

                    "productos": []

                })

            solicitud_editar = (

                SolicitudCotizacion.objects.filter(

                    usuario=request.user,

                    numero_usuario=numero_solicitud,

                    enviada=True

                ).first()

            )

            if solicitud_editar is None:

                return JsonResponse({

                    "ok": True,

                    "respuesta": (

                        f"No encontré una solicitud con "

                        f"el número {numero_solicitud}. "

                        "Verifica el número e inténtalo "

                        "nuevamente."

                    ),

                    "confirmado": False,

                    "accion": "ninguna",

                    "productos": []

                })

            if solicitud_editar.estado != "revision":

                return JsonResponse({

                    "ok": True,

                    "respuesta": (

                        "Esa solicitud ya fue procesada "

                        "y no puede editarse."

                    ),

                    "confirmado": False,

                    "accion": "ninguna",

                    "productos": []

                })

            if solicitud_editar.bloqueada:

                return JsonResponse({

                    "ok": True,

                    "respuesta": (

                        "Esa solicitud está siendo revisada "

                        "y no puede editarse en este momento."

                    ),

                    "confirmado": False,

                    "accion": "ninguna",

                    "productos": []

                })

            solicitud_editar.enviada = False

            solicitud_editar.save(

                update_fields=[

                    "enviada"

                ]

            )

            request.session[

                "piroia_solicitud_id"

            ] = solicitud_editar.id

            request.session[

                "solicitud_editando_id"

            ] = solicitud_editar.id

            # La solicitud ya existía; PiroIA solo la está editando.

            request.session[

                "piroia_creando_solicitud"

            ] = False

            # Guardar una copia de los productos originales
            # por si el usuario cancela la edición.
            productos_originales = []

            for detalle in (
                solicitud_editar.detalles
                .select_related("producto")
                .all()
            ):
                productos_originales.append({
                    "producto_id": detalle.producto.id,
                    "cantidad": detalle.cantidad,
                    "seleccionado": detalle.seleccionado
                })

            request.session[
                "piroia_productos_originales"
            ] = productos_originales

            request.session.modified = True

            request.session.modified = True

            resumen_editar = []

            for detalle in (

                solicitud_editar.detalles

                .select_related("producto")

                .all()

            ):

                resumen_editar.append(

                    f"{detalle.cantidad} "

                    f"{'pieza' if detalle.cantidad == 1 else 'piezas'} "

                    f"de {detalle.producto.nombre}"

                )

            productos_editar = []

            for detalle in (

                solicitud_editar.detalles

                .select_related("producto")

                .all()

            ):

                productos_editar.append({

                    "producto_id": detalle.producto.id,

                    "nombre": detalle.producto.nombre,

                    "cantidad": detalle.cantidad

                })

            return JsonResponse({

                "ok": True,

                "respuesta": (

                    f"Perfecto. Abrí tu solicitud "

                    f"{numero_solicitud} para editarla. "

                    "Actualmente contiene: "

                    +

                    ", ".join(

                        resumen_editar

                    )

                    +

                    ". Puedes decirme qué producto "

                    "o cantidad quieres cambiar."

                ),

                "confirmado": False,

                "accion": "editar",

                "productos": productos_editar,

                "solicitud_id": solicitud_editar.id,

                "numero_usuario": (

                    solicitud_editar.numero_usuario

                ),

                "redirect_url": reverse("solicitudes")

            })

        # ----------------------------------------------------------

        # CANCELAR SOLICITUD

        # ----------------------------------------------------------

        palabras_cancelar = [

            "cancela mi solicitud",

            "cancelar mi solicitud",

            "cancela la solicitud",

            "cancelar la solicitud",

            "quiero cancelar mi solicitud",

            "quiero cancelar la solicitud",

            "cancela esta solicitud",

            "cancelar esta solicitud",

            "quiero cancelar",

            "cancela esa solicitud",

            "cancelar esa solicitud",

            "cancela esa",

            "cancelar esa",

            "cancelala",

            "cancélala",

            "cancelalo",

            "cancélalo",

            "ya no la quiero",

            "ya no quiero la solicitud",

            "anula la solicitud",

            "anular la solicitud"

        ]

        if (

            modo == "solicitud"

            and any(

                palabra in pregunta_lower

                for palabra in palabras_cancelar

            )

        ):

            if solicitud_actual is None:

                return JsonResponse({

                    "ok": True,

                    "respuesta": (

                        "No tienes una solicitud activa "

                        "para cancelar."

                    ),

                    "confirmado": False,

                    "accion": "ninguna",

                    "productos": []

                })

            # Solo se elimina si PiroIA creó este borrador.

            # Si es una solicitud existente que se estaba editando,

            # nunca se elimina la solicitud original.

            es_nueva_piroia = request.session.get(

                "piroia_creando_solicitud",

                False

            )

            if es_nueva_piroia:

                # Si PiroIA creó una solicitud nueva,
                # al cancelarla se elimina el borrador.
                solicitud_actual.delete()

            else:

                # Si era una solicitud que ya existía,
                # restauramos exactamente los productos
                # y cantidades que tenía antes de comenzar la edición.

                productos_originales = request.session.get(
                    "piroia_productos_originales",
                    []
                )

                # Eliminar los detalles actuales de la solicitud.
                # Esto quita productos agregados durante la edición
                # y elimina cambios de cantidades.
                solicitud_actual.detalles.all().delete()

                # Volver a crear los detalles originales.
                for producto_original in productos_originales:

                    producto_id = producto_original.get(
                        "producto_id"
                    )

                    cantidad_original = producto_original.get(
                        "cantidad",
                        1
                    )

                    seleccionado_original = producto_original.get(
                        "seleccionado",
                        True
                    )

                    producto = (
                        Producto.objects
                        .filter(
                            id=producto_id,
                            estado=True
                        )
                        .first()
                    )

                    if not producto:
                        continue

                    DetalleSolicitud.objects.create(
                        solicitud=solicitud_actual,
                        producto=producto,
                        cantidad=cantidad_original,
                        seleccionado=seleccionado_original
                    )

                # La solicitud vuelve a quedar como estaba
                # antes de comenzar la edición.
                solicitud_actual.enviada = True
                solicitud_actual.bloqueada = False

                solicitud_actual.save(
                    update_fields=[
                        "enviada",
                        "bloqueada"
                    ]
                )

            request.session.pop(

                "piroia_solicitud_id",

                None

            )

            request.session.pop(

                "solicitud_editando_id",

                None

            )

            request.session.pop(

                "piroia_creando_solicitud",

                None

            )

            request.session.pop(
                "piroia_productos_originales",
                None
            )

            request.session.modified = True

            return JsonResponse({
                "ok": True,
                "respuesta": "Listo. La solicitud fue cancelada.",
                "confirmado": False,
                "accion": "cancelar",
                "productos": [],
                "cancelada": True,
                "redirect_url": (
                    reverse("mis_cotizaciones")
                    if es_edicion_existente
                    else reverse("solicitudes")
                )
            })

        # ----------------------------------------------------------

        # ENVIAR SOLICITUD

        # ----------------------------------------------------------

        # PiroIA puede realizar el envío definitivo SOLAMENTE

        # cuando el usuario ya se encuentra en Solicitudes.

        #

        # Si todavía está preparando la solicitud desde otro lugar,

        # "ya quedó" solamente la lleva a Solicitudes para revisión.

        # El botón "Enviar solicitud" sigue funcionando normalmente.

        # ----------------------------------------------------------



        palabras_enviar = [
            "envía mi solicitud",
            "enviar mi solicitud",
            "envía la solicitud",
            "enviar la solicitud",
            "quiero enviar mi solicitud",
            "quiero enviar la solicitud",
            "manda mi solicitud",
            "mandar mi solicitud",
            "puedes enviarla",
            "envíala",
            "enviála",
            "enviala",
            "ya puedes enviarla",
            "quiero enviarla",
            "ya quedó, envíala",
            "ya quedo, enviala",
            "enviar a cotización",
            "enviar a cotizacion",
            "manda a cotización",
            "manda a cotizacion",
            "enviar la cotización",
            "enviar la cotizacion"
        ]

        frases_confirmacion = [
            "ya quedó",
            "ya quedo",
            "así está bien",
            "asi esta bien",
            "está bien",
            "esta bien",
            "eso es todo",
            "confirmo"
        ]

        quiere_enviar = any(
            palabra in pregunta_lower
            for palabra in palabras_enviar
        )

        # Detectar frases como:
        # "sí, ya quedó, ya envíala a cotización"
        # "ya quedó, mándala a cotización"
        # "sí, ya está bien, envíala"
        quiere_enviar = (
            quiere_enviar
            or (
                (
                    "ya quedo" in pregunta_lower
                    or "ya quedó" in pregunta_lower
                    or "ya esta bien" in pregunta_lower
                    or "ya está bien" in pregunta_lower
                )
                and
                (
                    "envia" in pregunta_lower
                    or "envía" in pregunta_lower
                    or "enviar" in pregunta_lower
                    or "manda" in pregunta_lower
                    or "mandar" in pregunta_lower
                    or "cotizacion" in pregunta_lower
                    or "cotización" in pregunta_lower
                )
            )
        )

        confirma_en_solicitudes = any(
            frase in pregunta_lower
            for frase in frases_confirmacion
        )



        # ==========================================================
        # SI YA ESTÁ EN SOLICITUDES Y QUIERE ENVIAR
        # ==========================================================

        # "ya quedó" y frases similares NO envían la solicitud.
        # Solo una orden explícita como "envíala" puede hacerlo aquí.
        if (
            modo == "solicitud"
            and solicitud_actual is not None
            and en_solicitudes
            and quiere_enviar
        ):
            resultado_envio = enviar_solicitud(request)

            try:
                datos_envio = json.loads(
                    resultado_envio.content.decode("utf-8")
                )
            except Exception:
                datos_envio = {
                    "ok": False,
                    "mensaje": "No fue posible procesar el envío."
                }

            if not datos_envio.get("ok"):
                return JsonResponse({
                    "ok": False,
                    "respuesta": datos_envio.get(
                        "mensaje",
                        "No fue posible enviar la solicitud."
                    ),
                    "confirmado": False,
                    "accion": "ninguna",
                    "productos": []
                })

            return JsonResponse({
                "ok": True,
                "respuesta": (
                    "Perfecto. Tu solicitud fue enviada correctamente. "
                    "Puedes consultar su estado en Mis cotizaciones."
                ),
                "confirmado": True,
                "accion": "enviar",
                "productos": [],
                "redirect_url": reverse("mis_cotizaciones")
            })


        # SI TODAVÍA NO ESTÁ EN SOLICITUDES

        # ==========================================================



        if (

            modo == "solicitud"

            and quiere_enviar

        ):



            if solicitud_actual is None:

                return JsonResponse({

                    "ok": True,

                    "respuesta": (

                        "No tienes una solicitud activa para enviar. "

                        "Si deseas, puedo ayudarte a preparar una."

                    ),

                    "confirmado": False,

                    "accion": "ninguna",

                    "productos": []

                })



            productos_revision = []

            resumen_revision = []



            detalles_revision = (

                solicitud_actual.detalles

                .select_related("producto")

                .all()

            )



            for detalle in detalles_revision:



                productos_revision.append({

                    "producto_id": detalle.producto.id,

                    "nombre": detalle.producto.nombre,

                   "cantidad": detalle.cantidad

                })



                resumen_revision.append(

                    f"{detalle.cantidad} "

                    f"{'pieza' if detalle.cantidad == 1 else 'piezas'} "

                    f"de {detalle.producto.nombre}"

                )



            if resumen_revision:



                respuesta_revision = (

                    "Perfecto. Tu solicitud quedó preparada con "

                    + ", ".join(resumen_revision)

                    + ". Te llevaré al apartado de Solicitudes "

                    "para que puedas revisarla antes de enviarla."

                )



            else:



                respuesta_revision = (

                    "Tu solicitud está vacía. "

                    "Te llevaré al apartado de Solicitudes "

                    "para que puedas revisarla."

                )



            return JsonResponse({

                "ok": True,

                "respuesta": respuesta_revision,

                "confirmado": True,

                "accion": "revisar",

                "productos": productos_revision,

                "redirect_url": reverse(

                    "solicitudes"

                )

            })



        # ==========================================================

        # 7. INFORMACIÓN PARA GROQ

        # ==========================================================

        catalogo_texto = json.dumps(

            catalogo,

            ensure_ascii=False

        )

        solicitud_texto = json.dumps(

            productos_solicitud,

            ensure_ascii=False

        )

        historial_texto = json.dumps(

            historial_reciente,

            ensure_ascii=False

        )

        # ==========================================================

        # 8. REGLAS GENERALES

        # ==========================================================

        reglas_piroia = """

REGLAS OBLIGATORIAS:

\\- Responde siempre en español.

\\- Sé natural, claro y breve.

\\- Nunca muestres IDs de productos.

\\- Nunca muestres identificadores internos.

\\- Nunca muestres precios.

\\- Nunca muestres costos.

\\- Nunca muestres importes monetarios.

\\- El precio se determina mediante cotización.

\\- Utiliza siempre "pieza" o "piezas".

\\- Ejemplo correcto:

  "Agregué 3 piezas de Pachanga Plus."

\\- Ejemplo incorrecto:

  "Agregué ID 33 cantidad 3."

\\- No inventes productos.

\\- No inventes cantidades.

\\- Utiliza únicamente productos existentes en el catálogo.

\\- Si no estás seguro del producto, pide aclaración.

\\- No proporciones instrucciones para fabricar, modificar,

  combinar, manipular, encender o utilizar productos pirotécnicos.

\\- Tu función se limita al catálogo y solicitudes de cotización.

\- En "productos" incluye SOLAMENTE los productos que el usuario

  menciona, agrega, quita o modifica EN EL MENSAJE ACTUAL.



\- NO vuelvas a incluir productos que ya estaban en la solicitud

  si el usuario no los está modificando en este mensaje.



\- Si el usuario dice "agrega 2 de Pachanga Plus", devuelve solamente

  Pachanga Plus dentro de "productos".



\- Si el usuario dice "agrega 2 de Pachanga Plus y 3 de otro producto",

  devuelve únicamente esos productos.



\- Si el usuario indica una cantidad sin repetir el nombre del producto,

  utiliza el contexto de la conversación para identificar el producto

  al que se refiere.



\- NO devuelvas nuevamente todos los productos de la solicitud activa

  solamente porque ya forman parte de ella.



\- La cantidad de un producto en "productos" representa SOLAMENTE

  la cantidad que el usuario está agregando o modificando en el

  mensaje actual. No representa la cantidad total que ya existe.



\- Si el usuario dice "agrega 2 piezas", interpreta esas 2 piezas

  como una cantidad nueva que debe sumarse a la cantidad existente.

"""

        # ==========================================================
        # 9. PROMPT
        # ==========================================================

        tipo_solicitud = (
            "EDICIÓN DE UNA SOLICITUD EXISTENTE"
            if es_edicion_existente
            else "SOLICITUD NUEVA CREADA POR PIROIA"
        )


        # ==========================================================

        if modo == "solicitud":

            instrucciones = f"""

Eres PiroIA, el asistente inteligente de un catálogo web.

Tu función es ayudar con productos del catálogo y

solicitudes de cotización.

{reglas_piroia}

CATÁLOGO REAL:

{catalogo_texto}

TIPO DE SOLICITUD:

{tipo_solicitud}

SOLICITUD ACTIVA:

{solicitud_texto}

CONVERSACIÓN RECIENTE:

{historial_texto}

IMPORTANTE:

La conversación NO debe tratarse como mensajes aislados.

Utiliza el historial para entender frases como:

\\- "cada una"

\\- "los dos"

\\- "ese producto"

\\- "agrega otro"

\\- "quita uno"

\\- "sí"

\\- "sí por favor"

\\- "créala"

\\- "esa está bien"

\\- "así está bien"

\\- "eso es todo"

Si el usuario menciona primero un producto y después dice:

"quiero tres unidades"

interpreta la cantidad como:

3 piezas del producto mencionado anteriormente.

No vuelvas a preguntar el nombre si ya está claro.

Si existe una solicitud activa:

\\- trabaja sobre ESA solicitud;

\\- no cambies automáticamente a otra;

\\- conserva esa solicitud hasta que sea enviada o cancelada.

ACCIONES:

"agregar":

El usuario quiere agregar productos o aumentar cantidades.

"quitar":

El usuario quiere quitar productos o disminuir cantidades.

"cambiar":

El usuario quiere establecer una cantidad específica.

"ninguna":

No se debe modificar la solicitud.

CONFIRMACIÓN:

Si el usuario dice:

"no"

"así está bien"

"está bien"

"eso es todo"

"ya quedó"

"confirmo"

después de que el sistema le haya mostrado la solicitud, eso significa que terminó de preparar el borrador.

IMPORTANTE:

Eso NO significa enviar la solicitud.

Cuando el usuario confirme el borrador:

\\- confirmado=true

\\- NO envíes todavía

\\- devuelve el resumen

\\- el sistema llevará al usuario a Solicitudes

Si el usuario dice "envíala", "enviar mi solicitud", "manda mi solicitud" o "quiero enviarla", NO debes enviarla desde PiroIA.

Debes indicar que la solicitud está preparada y llevar al usuario al apartado de Solicitudes para que pueda revisarla y realizar el envío mediante el botón "Enviar solicitud".

El flujo obligatorio es:

PiroIA prepara o modifica -> Solicitudes -> usuario revisa -> usuario presiona "Enviar solicitud".

PiroIA nunca debe marcar una solicitud como enviada.



FORMATO OBLIGATORIO:

Responde ÚNICAMENTE con JSON válido:

{{

    "respuesta": "mensaje para el usuario",

    "accion": "agregar|quitar|cambiar|ninguna",

    "confirmado": false,

    "productos": [

        {{

            "producto_id": 1,

            "cantidad": 2

        }}

    ]

}}

REGLAS:

\\- producto_id es solamente para uso interno.

\\- Nunca escribas el ID dentro de "respuesta".

\\- "productos" debe contener únicamente productos reales.

\\- cantidad debe ser un número entero.

\\- No inventes cantidades.

\\- No inventes productos.

EJEMPLO:

Usuario:

"Quiero Pachanga Plus."

Respuesta:

{{

    "respuesta": "Claro. ¿Cuántas piezas de Pachanga Plus deseas incluir?",

    "accion": "ninguna",

    "confirmado": false,

    "productos": []

}}

Después:

Usuario:

"Quiero tres unidades."

Respuesta:

{{

    "respuesta": "Perfecto.",

    "accion": "agregar",

    "confirmado": false,

    "productos": [

        {{

            "producto_id": 33,

            "cantidad": 3

        }}

    ]

}}

El ID puede aparecer SOLO dentro de "productos".

Pregunta actual:

{pregunta}

"""

        else:

            instrucciones = f"""

Eres PiroIA, asistente inteligente de un catálogo web.

Tu función es CONSULTAR el catálogo.

{reglas_piroia}

CATÁLOGO REAL:

{catalogo_texto}

Puedes informar sobre:

\\- productos

\\- categorías

\\- descripciones

\\- características

\\- disponibilidad

Si el usuario pregunta por precios responde:

"El precio de los productos se determina mediante cotización.

Si deseas, puedo ayudarte a preparar una solicitud con la cantidad

que necesitas."

Nunca muestres precios.

Nunca muestres IDs.

Nunca proporciones instrucciones sobre fabricación,

modificación, combinación, manipulación, encendido o uso

de productos pirotécnicos.

Responde únicamente con JSON válido:

{{

    "respuesta": "mensaje para el usuario",

    "accion": "ninguna",

    "confirmado": false,

    "productos": []

}}

Pregunta:

{pregunta}

"""

        # ==========================================================

        # 10. GROQ

        # ==========================================================

        url = (

            "https://api.groq.com/openai/v1/chat/completions"

        )

        headers = {

            "Authorization": (

                f"Bearer {api_key}"

            ),

            "Content-Type": "application/json",

        }

        payload = {

            "model": "openai/gpt-oss-120b",

            "messages": [

                {

                    "role": "system",

                    "content": (

                        "Eres PiroIA, asistente inteligente "

                        "de un catálogo web. "

                        "Debes seguir exactamente las "

                        "instrucciones proporcionadas."

                    )

                },

                {

                    "role": "user",

                    "content": instrucciones

                }

            ],

            "temperature": 0.1,

            "max_tokens": 700,

            "reasoning_effort": "low",

            "response_format": {

                "type": "json_object"

            }

        }

        print(

            "===================================="

        )

        print(

            "PIROIA - GROQ"

        )

        print(

            "Pregunta:",

            pregunta

        )

        print(

            "Modo:",

            modo

        )

        print(

            "API KEY:",

            "SI" if api_key else "NO"

        )

        print(

            "===================================="

        )

        # ==========================================================

        # 11. LLAMAR A GROQ

        # ==========================================================

        try:

            respuesta_ia = requests.post(

                url,

                headers=headers,

                json=payload,

                timeout=(3, 15)

            )

        except requests.exceptions.Timeout:

            print(

                "GROQ TIMEOUT"

            )

            return JsonResponse({

                "ok": False,

                "respuesta": (

                    "PiroIA tardó demasiado en responder. "

                    "Intenta nuevamente."

                )

            })

        except requests.exceptions.RequestException as e:

            print(

                "ERROR DE CONEXIÓN GROQ:",

                str(e)

            )

            return JsonResponse({

                "ok": False,

                "respuesta": (

                    "No fue posible conectar con PiroIA "

                    "en este momento."

                )

            })

        print(

            "STATUS GROQ:",

            respuesta_ia.status_code

        )

        print(

            "RESPUESTA GROQ:",

            respuesta_ia.text[:2000]

        )

        # ==========================================================

        # 12. ERROR GROQ

        # ==========================================================

        if respuesta_ia.status_code != 200:

            try:

                error_data = (

                    respuesta_ia.json()

                )

                error_mensaje = (

                    error_data

                    .get("error", {})

                    .get("message")

                )

            except Exception:

                error_mensaje = None

            print(

                "ERROR GROQ:",

                error_mensaje

            )

            return JsonResponse({

                "ok": False,

                "respuesta": (

                    "PiroIA no pudo responder en "

                    "este momento. Intenta nuevamente."

                )

            })

        # ==========================================================

        # 13. EXTRAER CONTENIDO

        # ==========================================================

        try:

            resultado = (

                respuesta_ia.json()

            )

            choices = (

                resultado.get(

                    "choices",

                    []

                )

            )

            if not choices:

                raise ValueError(

                    "Groq no devolvió choices."

                )

            mensaje_ia = (

                choices[0]

                .get("message", {})

            )

            contenido = (

                mensaje_ia.get(

                    "content"

                )

            )

            if contenido is None:

                print(

                    "GROQ CONTENT = NONE"

                )

                return JsonResponse({

                    "ok": True,

                    "respuesta": (

                        "No pude terminar de interpretar "

                        "tu mensaje. Dime qué producto deseas "

                        "agregar o modificar y cuántas piezas "

                        "necesitas."

                    ),

                    "confirmado": False,

                    "accion": "ninguna",

                    "productos": []

                })

        except Exception as e:

            print(

                "ERROR LEYENDO GROQ:",

                str(e)

            )

            return JsonResponse({

                "ok": False,

                "respuesta": (

                    "PiroIA recibió una respuesta "

                    "que no pudo interpretar."

                )

            })

        contenido = (

            str(contenido)

            .strip()

        )

        if not contenido:

            return JsonResponse({

                "ok": True,

                "respuesta": (

                    "No pude interpretar la respuesta "

                    "de PiroIA. Intenta nuevamente."

                ),

                "confirmado": False,

                "accion": "ninguna",

                "productos": []

            })

        # ==========================================================

        # 14. MODO CONSULTA

        # ==========================================================

        if modo != "solicitud":

            if any(

                palabra in pregunta_lower

                for palabra in palabras_precio

            ):

                contenido = (

                    "El precio de los productos se determina "

                    "mediante cotización. Si deseas, puedo ayudarte "

                    "a preparar una solicitud con la cantidad "

                    "que necesitas."

                )

            return JsonResponse({

                "ok": True,

                "respuesta": contenido,

                "confirmado": False,

                "accion": "ninguna",

                "productos": []

            })

        # ==========================================================

        # 15. LIMPIAR JSON

        # ==========================================================

        contenido_json = contenido.strip()

        if contenido_json.startswith(

            "\\\`\\\`\\\`"

        ):

            contenido_json = (

                contenido_json

                .replace(

                    "\\\`\\\`\\\`json",

                    "",

                    1

                )

                .replace(

                    "\\\`\\\`\\\`",

                    ""

                )

                .strip()

            )

        try:

            resultado_ia = json.loads(

                contenido_json

            )

        except json.JSONDecodeError:

            inicio_json = (

                contenido_json.find("{")

            )

            fin_json = (

                contenido_json.rfind("}")

            )

            if (

                inicio_json != -1

                and fin_json > inicio_json

            ):

                posible_json = (

                    contenido_json[

                        inicio_json:

                        fin_json + 1

                    ]

                )

                try:

                    resultado_ia = json.loads(

                        posible_json

                    )

                except json.JSONDecodeError:

                    print(

                        "JSON INVÁLIDO DE GROQ:"

                    )

                    print(

                        contenido

                    )

                    return JsonResponse({

                        "ok": True,

                        "respuesta": (

                            "No pude interpretar correctamente "

                            "tu mensaje. Intenta decirme "

                            "el producto y la cantidad."

                        ),

                        "confirmado": False,

                        "accion": "ninguna",

                        "productos": []

                    })

            else:

                return JsonResponse({

                    "ok": True,

                    "respuesta": (

                        "No pude interpretar correctamente "

                        "tu mensaje. Intenta nuevamente."

                    ),

                    "confirmado": False,

                    "accion": "ninguna",

                    "productos": []

                })

        # ==========================================================

        # 16. DATOS DE LA IA

        # ==========================================================

        respuesta_texto = (

            resultado_ia.get(

                "respuesta",

                "Puedo ayudarte a preparar la solicitud."

            )

        )

        accion = (

            resultado_ia.get(

                "accion",

                "ninguna"

            )

        )

        confirmado = (

            resultado_ia.get(

                "confirmado",

                False

            )

        )

        productos = (

            resultado_ia.get(

                "productos",

                []

            )

        )

        if accion not in [

            "agregar",

            "quitar",

            "cambiar",

            "ninguna"

        ]:

            accion = "ninguna"

        confirmado = bool(
            confirmado
        )

        # Confirmaciones directas no dependen de que Groq las clasifique bien.
        if pregunta_lower.strip() in {
            "ya quedó", "ya quedo",
            "así está bien", "asi esta bien",
            "está bien", "esta bien",
            "eso es todo", "confirmo"
        }:
            confirmado = True
            accion = "ninguna"
            productos = []

        if not isinstance(

            productos,

            list

        ):

            productos = []

        # ==========================================================

        # 17. PROTECCIÓN CONTRA PRECIOS

        # ==========================================================

        if any(

            palabra in pregunta_lower

            for palabra in palabras_precio

        ):

            return JsonResponse({

                "ok": True,

                "respuesta": (

                    "El precio de los productos se determina "

                    "mediante cotización. Si deseas, puedo ayudarte "

                    "a preparar una solicitud con la cantidad "

                    "que necesitas."

                ),

                "confirmado": False,

                "accion": "ninguna",

                "productos": []

            })

        # ==========================================================

        # 18. CREAR SOLICITUD NUEVA

        # ==========================================================

        if (

            accion in [

                "agregar",

                "quitar",

                "cambiar"

            ]

            and productos

            and solicitud_actual is None

        ):

            solicitud_actual = (

                SolicitudCotizacion.objects.create(

                    usuario=request.user,

                    enviada=False,

                    estado="revision",

                    bloqueada=False

                )

            )

            request.session[

                "piroia_solicitud_id"

            ] = solicitud_actual.id

            request.session[

                "piroia_creando_solicitud"

            ] = True

            request.session.modified = True

        # ==========================================================
        # 19. APLICAR CAMBIOS
        # ==========================================================

        # La cantidad de "agregar" representa lo que el usuario quiere
        # SUMAR, no la cantidad total que ya existe.
        numeros_escritos = {
            "cero": 0, "uno": 1, "una": 1, "dos": 2, "tres": 3,
            "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7,
            "ocho": 8, "nueve": 9, "diez": 10, "once": 11,
            "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
            "dieciséis": 16, "dieciseis": 16, "diecisiete": 17,
            "dieciocho": 18, "diecinueve": 19, "veinte": 20
        }

        cantidad_explicita_usuario = None
        if accion == "agregar":
            import re
            patrones_cantidad = [
                r"(?:agrega|agregar|agregale|agrégale|añade|añadele|añádele|anade|anadele|suma|sumale|súmale|aumenta|aumentale|auméntale|ponle|pon|agregue)\s+(?:solo\s+|otras?\s+)?(\d+)",
                r"(?:agrega|agregar|agregale|agrégale|añade|añadele|añádele|anade|anadele|suma|sumale|súmale|aumenta|aumentale|auméntale|ponle|pon|agregue)\s+(?:solo\s+|otras?\s+)?(cero|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|dieciséis|dieciseis|diecisiete|dieciocho|diecinueve|veinte)\b",
                r"(?:quiero|necesito|dame)\s+(\d+)\s+(?:piezas?|unidades?)",
                r"(?:quiero|necesito|dame)\s+(cero|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|dieciséis|dieciseis|diecisiete|dieciocho|diecinueve|veinte)\b"
            ]
            for patron in patrones_cantidad:
                m=re.search(patron,pregunta_lower)
                if m:
                    valor=m.group(1)
                    cantidad_explicita_usuario=int(valor) if valor.isdigit() else numeros_escritos.get(valor)
                    if cantidad_explicita_usuario is not None:
                        break

        # ==========================================================

        # ==========================================================

        cambios_realizados = []

        if (

            solicitud_actual

            and accion in [

                "agregar",

                "quitar",

                "cambiar"

            ]

        ):

            for item in productos:

                try:

                    producto_id = int(

                        item.get(

                            "producto_id"

                        )

                    )

                    cantidad = int(

                        item.get(

                            "cantidad",

                            1

                        )

                    )

                except (

                    TypeError,

                    ValueError

                ):

                    continue

                if cantidad < 0:

                    continue

                producto = (

                    Producto.objects

                    .filter(

                        id=producto_id,

                        estado=True

                    )

                    .first()

                )

                if not producto:

                    continue

                detalle = (

                    DetalleSolicitud.objects

                    .filter(

                        solicitud=solicitud_actual,

                        producto=producto

                    )

                    .first()

                )

                # --------------------------------------------------

                # AGREGAR

                # --------------------------------------------------

                if accion == "agregar":



                    cantidad_agregada = max(
                        cantidad_explicita_usuario
                        if cantidad_explicita_usuario is not None
                        else cantidad,
                        1
                    )



                    # --------------------------------------------------

                    # EVITAR DUPLICAR PRODUCTOS QUE GROQ REPITA

                    # --------------------------------------------------



                    pregunta_actual = (

                        pregunta_lower

                        .strip()

                    )



                    nombre_producto_actual = (

                        producto.nombre

                        .lower()

                        .strip()

                    )



                    # Normalizamos algunos signos para comparar

                    # el nombre del producto con lo que escribió el usuario.

                    texto_comparacion = (

                        pregunta_actual

                        .replace(",", " ")

                        .replace(".", " ")

                        .replace("¿", " ")

                        .replace("?", " ")

                        .replace("¡", " ")

                        .replace("!", " ")

                    )



                    # --------------------------------------------------

                    # REVISAR QUÉ PRODUCTOS FUERON MENCIONADOS

                    # EN EL MENSAJE ACTUAL

                    # --------------------------------------------------



                    productos_mencionados = []



                    for otro_item in productos:



                        try:

                            otro_id = int(

                                otro_item.get(

                                    "producto_id"

                                )

                            )

                        except (

                            TypeError,

                            ValueError

                        ):

                            continue



                        otro_producto = (

                            Producto.objects

                            .filter(

                                id=otro_id,

                                estado=True

                            )

                            .first()

                        )



                        if not otro_producto:

                            continue



                        nombre_otro = (

                            otro_producto.nombre

                            .lower()

                            .strip()

                        )



                        if nombre_otro in texto_comparacion:

                            productos_mencionados.append(

                                otro_id

                            )



                    # --------------------------------------------------

                    # SI EL USUARIO MENCIONÓ PRODUCTOS EN ESTE MENSAJE,

                    # SOLO PROCESAMOS LOS QUE REALMENTE MENCIONÓ.

                    #

                    # Esto evita que Groq repita productos anteriores

                    # y que sus cantidades vuelvan a sumarse.

                    # --------------------------------------------------



                    if (
                        productos_mencionados
                        and producto.id not in productos_mencionados
                    ):
                        continue

                    # Si el usuario dijo "agrégale 2" sin repetir el nombre,
                    # usamos solo el primer producto identificado por el contexto.
                    if (
                        not productos_mencionados
                        and len(productos) > 1
                    ):
                        try:
                            primer_producto_id = int(productos[0].get("producto_id"))
                        except (TypeError, ValueError):
                            primer_producto_id = None
                        if primer_producto_id is not None and producto.id != primer_producto_id:
                            continue

                    # --------------------------------------------------
                    # AGREGAR PRODUCTO
                    # --------------------------------------------------
                    if detalle:

                        detalle.cantidad += (
                            cantidad_agregada
                        )
                        detalle.seleccionado = True
                        detalle.save()
                        cantidad_actual = (
                            detalle.cantidad

                        )
                    else:
                        DetalleSolicitud.objects.create(
                            solicitud=solicitud_actual,
                            producto=producto,
                            cantidad=cantidad_agregada,
                            seleccionado=True
                        )



                        cantidad_actual = (

                            cantidad_agregada

                        )



                    cambios_realizados.append(

                        f"Agregué "

                        f"{cantidad_agregada} "

                        f"{'pieza' if cantidad_agregada == 1 else 'piezas'} "

                        f"de {producto.nombre}. "

                        f"Ahora tienes "

                        f"{cantidad_actual} "

                        f"{'pieza' if cantidad_actual == 1 else 'piezas'}."

                    )

                # --------------------------------------------------

                # CAMBIAR

                # --------------------------------------------------

                elif accion == "cambiar":

                    if cantidad <= 0:

                        if detalle:

                            detalle.delete()

                        cambios_realizados.append(

                            f"Quité "

                            f"{producto.nombre} "

                            f"de la solicitud."

                        )

                    else:

                        if detalle:

                            detalle.cantidad = (

                                cantidad

                            )

                            detalle.seleccionado = True

                            detalle.save()

                        else:

                            DetalleSolicitud.objects.create(

                                solicitud=solicitud_actual,

                                producto=producto,

                                cantidad=cantidad,

                                seleccionado=True

                            )

                        cambios_realizados.append(

                            f"Cambié "

                            f"{producto.nombre} "

                            f"a "

                            f"{cantidad} "

                            f"{'pieza' if cantidad == 1 else 'piezas'}."

                        )

                # --------------------------------------------------

                # QUITAR

                # --------------------------------------------------

                elif accion == "quitar":

                    if not detalle:

                        cambios_realizados.append(

                            f"{producto.nombre} "

                            "no estaba en la solicitud."

                        )

                        continue

                    if cantidad >= detalle.cantidad:

                        detalle.delete()

                        cambios_realizados.append(

                            f"Quité "

                            f"{producto.nombre} "

                            "de la solicitud."

                        )

                    else:

                        detalle.cantidad -= (

                            cantidad

                        )

                        if detalle.cantidad <= 0:

                            detalle.delete()

                            cambios_realizados.append(

                                f"Quité "

                                f"{producto.nombre} "

                                "de la solicitud."

                            )

                        else:

                            detalle.save()

                            cambios_realizados.append(

                                f"Quité "

                                f"{cantidad} "

                                f"{'pieza' if cantidad == 1 else 'piezas'} "

                                f"de {producto.nombre}. "

                                f"Ahora quedan "

                                f"{detalle.cantidad} "

                                f"{'pieza' if detalle.cantidad == 1 else 'piezas'}."

                            )

        # ==========================================================
        # 20. CONFIRMACIÓN
        # ==========================================================

        if confirmado and solicitud_actual:
            detalles_finales = (
                solicitud_actual.detalles
                .select_related("producto")
                .all()
            )

            productos_finales = []
            resumen_productos = []

            for detalle in detalles_finales:
                imagen_url = ""
                try:
                    imagen = detalle.producto.imagenes.first()
                    if imagen and imagen.imagen:
                        imagen_url = imagen.imagen.url
                except Exception:
                    imagen_url = ""

                productos_finales.append({
                    "producto_id": detalle.producto.id,
                    "nombre": detalle.producto.nombre,
                    "cantidad": detalle.cantidad,
                    "imagen": imagen_url
                })

                resumen_productos.append(
                    f"{detalle.cantidad} "
                    f"{'pieza' if detalle.cantidad == 1 else 'piezas'} "
                    f"de {detalle.producto.nombre}"
                )

            if es_edicion_existente:
                solicitud_actual.enviada = True
                solicitud_actual.bloqueada = False
                solicitud_actual.estado = "revision"
                solicitud_actual.save(
                    update_fields=["enviada", "bloqueada", "estado"]
                )

                request.session.pop("solicitud_editando_id", None)
                request.session.pop("piroia_solicitud_id", None)
                request.session.pop("piroia_creando_solicitud", None)
                request.session.modified = True

                return JsonResponse({
                    "ok": True,
                    "respuesta": (
                        "Perfecto. Los cambios quedaron guardados en tu solicitud. "
                        "Te llevaré a Mis cotizaciones para consultar la solicitud actualizada."
                    ),
                    "confirmado": True,
                    "accion": accion,
                    "productos": productos_finales,
                    "redirect_url": reverse("mis_cotizaciones")
                })

            # Solicitud nueva: "ya quedó" solo termina la preparación.
            respuesta_confirmacion = (
                "Perfecto. Tu solicitud quedó preparada con "
                + (", ".join(resumen_productos) if resumen_productos else "ningún producto")
                + ". No se ha enviado todavía. Te llevaré al apartado de Solicitudes para revisarla."
            )

            return JsonResponse({
                "ok": True,
                "respuesta": respuesta_confirmacion,
                "confirmado": True,
                "accion": accion,
                "productos": productos_finales,
                "redirect_url": reverse("solicitudes")
            })

        # ==========================================================

        # 21. SOLICITUD PREPARADA

        # ==========================================================

        if (

            solicitud_actual

            and cambios_realizados

            and not confirmado

        ):

            detalles_preparados = (

                solicitud_actual.detalles

                .select_related(

                    "producto"

                )

                .all()

            )

            resumen_preparado = []

            productos_preparados = []

            for detalle in detalles_preparados:

                resumen_preparado.append(

                    f"{detalle.cantidad} "

                    f"{'pieza' if detalle.cantidad == 1 else 'piezas'} "

                    f"de {detalle.producto.nombre}"

                )

                productos_preparados.append({

                    "producto_id": (

                        detalle.producto.id

                    ),

                    "nombre": (

                        detalle.producto.nombre

                    ),

                    "cantidad": (

                        detalle.cantidad

                    )

                })

            if resumen_preparado:

                respuesta_preparada = (

                    "Perfecto. Preparé tu solicitud con "

                    +

                    ", ".join(

                        resumen_preparado

                    )

                    +

                    ". ¿Deseas agregar o modificar "

                    "algún producto o cantidad?"

                )

            else:

                respuesta_preparada = (

                    "La solicitud quedó sin productos. "

                    "¿Deseas agregar algún producto?"

                )

            return JsonResponse({

                "ok": True,

                "respuesta": respuesta_preparada,

                "confirmado": False,

                "accion": accion,

                "productos": productos_preparados

            })

        # ==========================================================

        # 22. RESPUESTA NORMAL

        # ==========================================================

        productos_actualizados = []

        if solicitud_actual:

            detalles_actualizados = (

                solicitud_actual.detalles

                .select_related(

                    "producto"

                )

                .all()

            )

            for detalle in detalles_actualizados:

                imagen_url = ""

                try:

                    imagen = (

                        detalle.producto

                        .imagenes

                        .first()

                    )

                    if (

                        imagen

                        and imagen.imagen

                    ):

                        imagen_url = (

                            imagen.imagen.url

                        )

                except Exception:

                    imagen_url = ""

                productos_actualizados.append({

                    "producto_id": (

                        detalle.producto.id

                    ),

                    "nombre": (

                        detalle.producto.nombre

                    ),

                    "cantidad": (

                        detalle.cantidad

                    ),

                    "imagen": imagen_url

                })

        # ----------------------------------------------------------

        # MENSAJE GENERADO POR EL SERVIDOR

        # ----------------------------------------------------------

        if cambios_realizados:

            respuesta_texto = " ".join(

                cambios_realizados

            )

        # ----------------------------------------------------------

        # LIMPIAR IDs DEL TEXTO DE RESPUESTA

        # ----------------------------------------------------------

        # Por seguridad, nunca dejamos que una respuesta

        # de la IA muestre identificadores internos.

        import re

        respuesta_texto = re.sub(

            r"\bID\s\\\*[:#]?\s\\\*\d+\b",

            "",

            str(respuesta_texto),

            flags=re.IGNORECASE

        )

        respuesta_texto = re.sub(

            r"\bproducto\s+ID\s\\\*[:#]?\s\\\*\d+\b",

            "",

            respuesta_texto,

            flags=re.IGNORECASE

        )

        return JsonResponse({

            "ok": True,

            "respuesta": respuesta_texto,

            "confirmado": False,

            "accion": accion,

            "productos": productos_actualizados

        })

    # ==============================================================

    # ERROR JSON

    # ==============================================================

    except json.JSONDecodeError:

        return JsonResponse({

            "ok": False,

            "respuesta": (

                "La solicitud enviada no tiene "

                "un formato válido."

            )

        }, status=400)

    # ==============================================================

    # ERROR GENERAL

    # ==============================================================

    except Exception as e:

        print(

            "===================================="

        )

        print(

            "ERROR GENERAL PIROIA"

        )

        print(

            str(e)

        )

        print(

            "===================================="

        )

        return JsonResponse({

            "ok": False,

            "respuesta": (

                "Ocurrió un problema al procesar "

                "tu solicitud."

            )

        }, status=500)


def registrar_actividad(usuario, accion, descripcion):
    RegistroActividad.objects.create(
        usuario=(
            usuario
            if usuario and usuario.is_authenticated
            else None
        ),
        accion=accion,
        descripcion=descripcion
    )




@csrf_exempt
def recibir_medicion_iot(request):
    if request.method != 'POST':
        return JsonResponse(
            {'error': 'Método no permitido'},
            status=405
        )

    try:
        datos = json.loads(request.body)

        dispositivo = datos.get(
            'dispositivo',
            'Sensor IoT de demostración'
        )
        temperatura = float(datos['temperatura'])
        humedad = float(datos['humedad'])

        if not (-40 <= temperatura <= 100):
            return JsonResponse(
                {'error': 'Temperatura fuera de rango'},
                status=400
            )

        if not (0 <= humedad <= 100):
            return JsonResponse(
                {'error': 'Humedad fuera de rango'},
                status=400
            )

        # Guardar la medición recibida
        medicion = MedicionIoT.objects.create(
            dispositivo=dispositivo,
            temperatura=temperatura,
            humedad=humedad
        )

        alertas = []

        # Solo la temperatura crítica genera correo.
        # Este umbral es únicamente para pruebas.
        temperatura_critica = settings.IOT_TEMPERATURA_CRITICA
        clave_alerta = f'iot_alerta_critica_{dispositivo}'

        if temperatura >= temperatura_critica:
            alertas.append('Temperatura crítica')

            # Evitar repetir el correo mientras la alerta siga activa
            if not cache.get(clave_alerta, False):
                asunto = (
                    f'ALERTA CRÍTICA DE TEMPERATURA - {dispositivo}'
                )

                contenido = f"""
                <div style="font-family:Arial,sans-serif; max-width:650px;
                    margin:auto; border-radius:18px; overflow:hidden;
                    border:1px solid #e5e7eb;">

                    <div style="background:#111827; padding:30px;
                        text-align:center;">
                        <h1 style="color:#D4AF37; margin:0;">
                            Cooperativa Pirotécnica
                        </h1>
                        <p style="color:white; margin-top:8px;">
                            Catálogo Web · Monitoreo IoT
                        </p>
                    </div>

                    <div style="padding:35px;">
                        <h2 style="color:#b91c1c;">
                            ¡Alerta crítica de temperatura!
                        </h2>

                        <p style="font-size:16px; color:#4b5563;
                            line-height:1.7;">
                            El dispositivo <strong>{dispositivo}</strong>
                            registró una temperatura igual o superior
                            al umbral crítico configurado.
                        </p>

                        <div style="background:#fff7ed;
                            border-left:5px solid #D4AF37;
                            padding:18px; margin:25px 0;">
                            <strong>Datos de la medición</strong>
                            <ul style="line-height:1.9;">
                                <li>Temperatura:
                                    <strong>{temperatura} °C</strong>
                                </li>
                                <li>Umbral configurado:
                                    {temperatura_critica} °C
                                </li>
                                <li>Humedad: {humedad}%</li>
                                <li>Fecha: {medicion.fecha}</li>
                            </ul>
                        </div>

                        <p style="color:#4b5563; line-height:1.7;">
                            Revisa el estado del dispositivo y sigue
                            los procedimientos de seguridad establecidos
                            para las instalaciones.
                        </p>

                        <p style="font-size:13px; color:#6b7280;">
                            Esta alerta es una función de apoyo del
                            sistema y no sustituye los equipos de
                            seguridad ni los procedimientos de emergencia.
                        </p>
                    </div>

                    <div style="background:#111827; color:white;
                        text-align:center; padding:18px;">
                        © Cooperativa Pirotécnica · Catálogo Web
                    </div>
                </div>
                """

                enviado = enviar_correo(
                    settings.IOT_ALERT_EMAIL,
                    asunto,
                    contenido
                )

                if enviado:
                    # La alerta no se repite mientras siga activa.
                    cache.set(clave_alerta, True, timeout=None)

        else:
            # Permitir una nueva alerta si vuelve a ser crítica
            cache.delete(clave_alerta)

        return JsonResponse({
            'mensaje': 'Medición recibida correctamente',
            'id': medicion.id,
            'dispositivo': medicion.dispositivo,
            'temperatura': medicion.temperatura,
            'humedad': medicion.humedad,
            'alertas': alertas,
            'fecha': medicion.fecha.isoformat()
        }, status=201)

    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return JsonResponse(
            {'error': 'Los datos enviados no son válidos'},
            status=400
        )




@login_required
def monitoreo_iot(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('inicio')

    mediciones = MedicionIoT.objects.all()[:20]
    ultima_medicion = mediciones.first()

    contexto = {
        'mediciones': mediciones,
        'ultima_medicion': ultima_medicion,
        'total_mediciones': MedicionIoT.objects.count(),

        'temperatura_min': settings.IOT_TEMPERATURA_MIN,
        'temperatura_max': settings.IOT_TEMPERATURA_MAX,
        'temperatura_critica': settings.IOT_TEMPERATURA_CRITICA,
        'humedad_min': settings.IOT_HUMEDAD_MIN,
        'humedad_max': settings.IOT_HUMEDAD_MAX,
    }

    return render(
        request,
        'admin/monitoreo_iot.html',
        contexto
    )



from django.core.mail import EmailMultiAlternatives
from django.utils.html import escape




def notificar_nueva_solicitud(solicitud):
    usuario = solicitud.usuario

    nombre_usuario = escape(
        usuario.get_full_name() or usuario.username
    )
    correo_usuario = escape(usuario.email or "No proporcionado")
    numero_usuario = escape(str(solicitud.numero_usuario or "No asignado"))
    estado = escape(solicitud.get_estado_display())
    fecha = solicitud.fecha.strftime("%d/%m/%Y a las %H:%M")

    asunto = f"Nueva solicitud de cotización #{solicitud.id}"

    # Versión de texto por si el correo no admite HTML.
    mensaje_texto = (
        "CATÁLOGO WEB\n\n"
        "Nueva solicitud de cotización\n\n"
        f"Solicitud: #{solicitud.id}\n"
        f"Número del usuario: {numero_usuario}\n"
        f"Usuario: {nombre_usuario}\n"
        f"Correo: {correo_usuario}\n"
        f"Estado: {estado}\n"
        f"Fecha: {fecha}\n\n"
        "Ingresa al sistema para revisar la solicitud."
    )

    # Versión HTML del correo.
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nueva solicitud de cotización</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f1f4f8;
                 font-family:Arial,Helvetica,sans-serif; color:#243047;">

        <table role="presentation" width="100%" cellspacing="0"
               cellpadding="0" border="0"
               style="background-color:#f1f4f8; padding:30px 12px;">
            <tr>
                <td align="center">

                    <table role="presentation" width="600" cellspacing="0"
                           cellpadding="0" border="0"
                           style="width:100%; max-width:600px; background:#ffffff;
                                  border-radius:14px; overflow:hidden;">

                        <tr>
                            <td style="background:#101c35; padding:28px 24px;
                                       text-align:center; border-bottom:4px solid #c9a64b;">
                                <div style="font-size:13px; letter-spacing:3px;
                                            color:#e2c875; font-weight:bold;">
                                    CATÁLOGO WEB
                                </div>
                                <h1 style="margin:14px 0 6px; font-size:24px;
                                           line-height:1.3; color:#ffffff;">
                                    Nueva solicitud de cotización
                                </h1>
                                <p style="margin:0; font-size:14px; color:#d8deea;">
                                    Se ha recibido una nueva solicitud en el sistema
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:28px 24px 12px;">
                                <p style="margin:0 0 8px; font-size:15px;">
                                    Hola, administrador:
                                </p>
                                <p style="margin:0; color:#647087;
                                          font-size:14px; line-height:1.7;">
                                    Un usuario acaba de enviar una solicitud de
                                    cotización. Estos son los datos para identificarla.
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:16px 24px;">
                                <table role="presentation" width="100%"
                                       cellspacing="0" cellpadding="0" border="0"
                                       style="background:#f8f7f2; border:1px solid #eee7d4;
                                              border-radius:10px;">
                                    <tr>
                                        <td style="padding:18px;">
                                            <p style="margin:0 0 5px; color:#7b8494;
                                                      font-size:12px; text-transform:uppercase;
                                                      letter-spacing:1px;">
                                                Número de solicitud
                                            </p>
                                            <p style="margin:0; font-size:27px;
                                                      font-weight:bold; color:#101c35;">
                                                #{solicitud.id}
                                            </p>
                                        </td>
                                        <td align="right" style="padding:18px;">
                                            <span style="display:inline-block;
                                                         background:#fff0c2; color:#76570b;
                                                         padding:8px 12px; border-radius:20px;
                                                         font-size:12px; font-weight:bold;">
                                                {estado}
                                            </span>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:0 24px 24px;">
                                <table role="presentation" width="100%"
                                       cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                        <td style="padding:13px 0; border-bottom:1px solid #edf0f4;
                                                   color:#778196; font-size:13px; width:42%;">
                                            Número del usuario
                                        </td>
                                        <td style="padding:13px 0; border-bottom:1px solid #edf0f4;
                                                   color:#243047; font-size:14px; font-weight:bold;">
                                            {numero_usuario}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:13px 0; border-bottom:1px solid #edf0f4;
                                                   color:#778196; font-size:13px;">
                                            Nombre del usuario
                                        </td>
                                        <td style="padding:13px 0; border-bottom:1px solid #edf0f4;
                                                   color:#243047; font-size:14px;">
                                            {nombre_usuario}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:13px 0; border-bottom:1px solid #edf0f4;
                                                   color:#778196; font-size:13px;">
                                            Correo electrónico
                                        </td>
                                        <td style="padding:13px 0; border-bottom:1px solid #edf0f4;
                                                   color:#243047; font-size:14px; overflow-wrap:anywhere;">
                                            {correo_usuario}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:13px 0; color:#778196; font-size:13px;">
                                            Fecha de envío
                                        </td>
                                        <td style="padding:13px 0; color:#243047; font-size:14px;">
                                            {fecha}
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:20px 24px; background:#f7f8fb;
                                       border-top:1px solid #edf0f4; text-align:center;">
                                <p style="margin:0 0 7px; font-size:13px;
                                          color:#46516a;">
                                    Ingresa a Catálogo Web para revisar los detalles
                                    y continuar con la solicitud.
                                </p>
                                <p style="margin:0; font-size:12px; color:#8a93a3;">
                                    Notificación automática del sistema Catálogo Web
                                </p>
                            </td>
                        </tr>

                    </table>

                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    correo = EmailMultiAlternatives(
        subject=asunto,
        body=mensaje_texto,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.IOT_ALERT_EMAIL],
    )
    correo.attach_alternative(html, "text/html")
    correo.send(fail_silently=False)




@login_required
@require_GET
def api_notificaciones_cotizaciones(request):
    # Solo el personal administrativo puede consultar la API.
    if not request.user.is_staff:
        return JsonResponse({
            "ok": False,
            "mensaje": "No tienes permiso para consultar las notificaciones."
        }, status=403)

    solicitudes = (
        SolicitudCotizacion.objects
        .filter(enviada=True)
        .select_related("usuario")
        .order_by("-fecha")[:20]
    )

    notificaciones = []

    for solicitud in solicitudes:
        notificaciones.append({
            "solicitud_id": solicitud.id,
            "numero_usuario": solicitud.numero_usuario,
            "usuario": (
                solicitud.usuario.get_full_name()
                or solicitud.usuario.username
            ),
            "correo": solicitud.usuario.email,
            "fecha": solicitud.fecha.isoformat(),
            "estado": solicitud.estado,
            "estado_texto": solicitud.get_estado_display(),
            "mensaje": (
                f"Se recibió la solicitud de cotización "
                f"#{solicitud.id}."
            )
        })

    return JsonResponse({
        "ok": True,
        "total": len(notificaciones),
        "notificaciones": notificaciones
    })

