from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.paginator import Paginator

from .forms import RegistroForm
from .models import DetalleSolicitud, Favorito, Producto, Perfil

from .forms_producto import ProductoForm
from .models import Producto

from .forms_categoria import CategoriaForm
from .models import Categoria

from .forms_imagen import ProductoImagenForm
from .models import ProductoImagen


from .models import ProductoImagen

from django.contrib import messages

from django.db.models import Count

from django.contrib.auth.models import User

from .models import SolicitudCotizacion

from django.http import JsonResponse

from django.contrib.admin.views.decorators import staff_member_required

from django.shortcuts import get_object_or_404, render


from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.conf import settings
import os

@login_required
def inicio(request):


    productos_destacados = Producto.objects.filter(
        estado=True,
        destacado=True
    ).order_by('-id')[:6]

    categorias_destacadas = Categoria.objects.filter(
        destacada=True
    ).order_by('-id')[:3]

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


def registro(request):

    if request.method == 'POST':

        form = RegistroForm(request.POST)

        if form.is_valid():

            usuario = form.save()

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

            return redirect('/accounts/login/')

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

    return render(request,
                  'admin/panel_admin.html',
                  {
                      'total_productos': total_productos,
                      'total_categorias': total_categorias
                  })

from django.core.paginator import Paginator

@login_required
def lista_productos(request):

    productos = Producto.objects.all().order_by('-id')

    # agregar primera imagen
    for producto in productos:
        producto.imagen_principal = producto.imagenes.first()

    paginator = Paginator(productos, 6)

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

            form.save()

            imagenes = request.FILES.getlist('imagen')

            for imagen in imagenes:

                ProductoImagen.objects.create(
                    producto=producto,
                    imagen=imagen
                )

            return redirect('lista_productos')

    else:

        form = ProductoForm(instance=producto)

    imagenes = ProductoImagen.objects.filter(
        producto=producto
    )

    return render(
        request,
        'admin/productos/editar.html',
        {
            'form': form,
            'producto': producto,
            'imagenes': imagenes
        }
    )


@login_required
def eliminar_imagen(request, id):

    imagen = ProductoImagen.objects.get(id=id)

    producto_id = imagen.producto.id

    imagen.delete()

    return redirect(f'/panel/productos/?editar={producto_id}')


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

    paginator = Paginator(categorias_lista, 5)

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

        form = CategoriaForm(request.POST)

        if form.is_valid():

            categoria = form.save()

            messages.success(
                request,
                f'Categoría "{categoria.nombre}" creada correctamente.'
            )

            return redirect('lista_categorias')

    else:

        form = CategoriaForm()

    return render(request,
                  'admin/categorias/agregar.html',
                  {
                      'form': form
                  })


@login_required
def editar_categoria(request, id):

    categoria = Categoria.objects.get(id=id)

    if request.method == 'POST':

        categoria.nombre = request.POST.get('nombre')
        categoria.descripcion = request.POST.get('descripcion')
        categoria.destacada = request.POST.get('destacada') == 'on'

        categoria.save()

        messages.success(
            request,
            'Categoría actualizada correctamente.'
        )

    return redirect('lista_categorias')


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

    total_productos = Producto.objects.count()

    total_categorias = Categoria.objects.count()

    productos_activos = Producto.objects.filter(
        estado=True
    ).count()

    productos_inactivos = Producto.objects.filter(
        estado=False
    ).count()

    ultimos_productos = Producto.objects.order_by('-id')[:5]

    return render(
        request,
        'admin/dashboard/dashboard.html',
        {
            'total_productos': total_productos,
            'total_categorias': total_categorias,
            'productos_activos': productos_activos,
            'productos_inactivos': productos_inactivos,
            'ultimos_productos': ultimos_productos
        }
    )


@login_required
def lista_usuarios(request):

    usuarios_lista = User.objects.select_related(
        'perfil'
    ).all().order_by('username')

    paginator = Paginator(
        usuarios_lista,
        5
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

    solicitudes = SolicitudCotizacion.objects.all().order_by("-fecha")

    pendientes = solicitudes.filter(
        estado="revision"
    ).count()

    cotizadas = solicitudes.filter(
        estado="cotizada"
    ).count()

    rechazadas = solicitudes.filter(
        estado="rechazada"
    ).count()

    abrir_modal = request.session.pop("abrir_modal", None)


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

def productos_por_categoria(request, id):

    categoria = Categoria.objects.get(id=id)

    productos_lista = Producto.objects.filter(
        categoria=categoria,
        estado=True
    ).order_by('-id')

    paginator = Paginator(productos_lista, 6)

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
            'favoritos_ids': favoritos_ids
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

    producto = Producto.objects.get(id=producto_id)

    solicitud, creada = SolicitudCotizacion.objects.get_or_create(
        usuario=request.user,
        enviada=False
    )

    detalle, creado = DetalleSolicitud.objects.get_or_create(
        solicitud=solicitud,
        producto=producto
    )

    if not creado:
        detalle.cantidad += 1
        detalle.save()

    return redirect('solicitudes')


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

    solicitud = SolicitudCotizacion.objects.filter(
        usuario=request.user,
        enviada=False
    ).first()

    if solicitud and not solicitud.detalles.exists():
        solicitud.delete()
        solicitud = None

    return render(
        request,
        'sistema/solicitudes.html',
        {
            'solicitud': solicitud
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


@login_required
def enviar_solicitud(request):

    solicitud = SolicitudCotizacion.objects.filter(
        usuario=request.user,
        enviada=False
    ).first()

    if solicitud is None:
        return JsonResponse({
            "ok": False,
            "mensaje": "No existe una solicitud activa."
        })

    if not solicitud.detalles.exists():
        return JsonResponse({
            "ok": False,
            "mensaje": "No hay productos en la solicitud."
        })

    solicitud.enviada = True
    solicitud.save()

    return JsonResponse({
        "ok": True
    })


@login_required
def mis_cotizaciones(request):

    solicitudes = SolicitudCotizacion.objects.filter(
        usuario=request.user,
        enviada=True
    ).order_by("-fecha")

    return render(
        request,
        "sistema/mis_cotizaciones.html",
        {
            "solicitudes": solicitudes
        }
    )


@staff_member_required
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

@login_required
def generar_cotizacion(request, id):

    solicitud = get_object_or_404(
        SolicitudCotizacion,
        id=id
    )

    if request.method == "POST":

        for detalle in solicitud.detalles.all():

            precio = request.POST.get(f"precio_{detalle.id}")

            # Si no se capturó un precio
            if not precio or precio.strip() == "":
                messages.error(
                    request,
                    f"El producto '{detalle.producto.nombre}' no tiene precio asignado."
                )

                request.session["abrir_modal"] = solicitud.id
                return redirect("lista_solicitudes")

            try:
                detalle.precio_aplicado = Decimal(precio)
                detalle.save()

            except InvalidOperation:
                messages.error(
                    request,
                    f"El precio del producto '{detalle.producto.nombre}' es inválido."
                )

                request.session["abrir_modal"] = solicitud.id
                return redirect("lista_solicitudes")
        # Todo salió bien
        solicitud.estado = "cotizada"
        solicitud.save()

        try:
            pdf_response = descargar_cotizacion_pdf(request, solicitud.id)
            pdf_bytes = pdf_response.content

            enviar_cotizacion(
                solicitud.usuario.email,
                pdf_bytes,
                solicitud.id,
            )

            messages.success(
                request,
                "La cotización fue generada y enviada correctamente al cliente."
            )

        except Exception as e:
            print("Error enviando correo:", e)

            messages.warning(
                request,
                "La cotización se generó correctamente, pero ocurrió un problema al enviar el correo."
            )

        return redirect("lista_solicitudes")
    


@login_required
def rechazar_cotizacion(request, id):

    solicitud = get_object_or_404(
        SolicitudCotizacion,
        id=id
    )

    solicitud.estado = "rechazada"
    solicitud.save()

    try:
        enviar_correo_rechazo(
            solicitud.usuario.email,
            solicitud.id
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

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="cotizacion_{solicitud.id}.pdf"'
    )

    pdf = canvas.Canvas(response, pagesize=letter)

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

    pdf.setFont("Helvetica-Bold", 17)

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

    pdf.setFont("Helvetica", 10)

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

    # línea roja
    pdf.setStrokeColorRGB(0.75, 0, 0)
    pdf.setLineWidth(2)

    pdf.line(
        30,
        height - 105,
        width - 30,
        height - 105
    )

    # ==========================
    # TITULO
    # ==========================

    pdf.setFillColorRGB(0, 0, 0)

    pdf.setFont("Helvetica-Bold", 18)

    pdf.drawCentredString(
        width / 2,
        height - 145,
        "COTIZACIÓN"
    )

    pdf.setFont("Helvetica", 11)

    pdf.drawString(
        40,
        height - 175,
        f"No. {solicitud.id}"
    )

    pdf.drawString(
        40,
        height - 195,
        f"Cliente: {solicitud.usuario.username}"
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

    pdf.setFillColorRGB(0.90, 0.90, 0.90)

    pdf.rect(
        35,
        y,
        540,
        22,
        fill=1
    )

    pdf.setFillColorRGB(0, 0, 0)

    pdf.setFont("Helvetica-Bold", 10)

    pdf.drawString(45, y + 7, "Producto")
    pdf.drawString(315, y + 7, "Cantidad")
    pdf.drawString(395, y + 7, "Precio")
    pdf.drawString(485, y + 7, "Subtotal")

    y -= 20

    total = 0

    pdf.setFont("Helvetica", 10)

    for detalle in solicitud.detalles.all():

        precio = float(detalle.precio_aplicado or 0)

        subtotal = precio * detalle.cantidad

        total += subtotal

        pdf.drawString(
            45,
            y,
            detalle.producto.nombre[:45]
        )

        pdf.drawString(
            330,
            y,
            str(detalle.cantidad)
        )

        pdf.drawString(
            395,
            y,
            f"${precio:,.2f}"
        )

        pdf.drawString(
            485,
            y,
            f"${subtotal:,.2f}"
        )

        y -= 18

    # ==========================
    # TOTAL
    # ==========================

    y -= 20

    pdf.setFont("Helvetica-Bold", 14)

    pdf.drawRightString(
        560,
        y,
        f"TOTAL: ${total:,.2f}"
    )

    # ==========================
    # OBSERVACIONES
    # ==========================

    y -= 45

    pdf.setFont("Helvetica", 10)

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

    pdf.setStrokeColorRGB(0.75, 0, 0)

    pdf.line(
        30,
        65,
        width - 30,
        65
    )

    pdf.setFont("Helvetica", 8)

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