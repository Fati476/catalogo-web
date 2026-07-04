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

import json

from .models import Perfil

from django.views.decorators.http import require_POST
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.conf import settings
import os

from .utils import enviar_correo

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

        request.session["solicitud_editando_id"] = solicitud.id

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

    if solicitud and not solicitud.detalles.exists():

        if request.session.get("solicitud_editando_id") == solicitud.id:
            pass

        else:
            solicitud.delete()
            request.session.pop("solicitud_editando_id", None)
            solicitud = None

    total_productos = 0
    total_unidades = 0

    if solicitud:
        total_productos = solicitud.detalles.count()
        total_unidades = sum(
            detalle.cantidad for detalle in solicitud.detalles.all()
        )

    return render(
        request,
        'sistema/solicitudes.html',
        {
            'solicitud': solicitud,
            'total_productos': total_productos,
            'total_unidades': total_unidades,
            'editando': solicitud_id is not None,
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
        return JsonResponse({
            "ok": False,
            "mensaje": "No existe una solicitud activa."
        })

    detalles_seleccionados = solicitud.detalles.filter(
        seleccionado=True
    )

    if not detalles_seleccionados.exists():
        return JsonResponse({
            "ok": False,
            "mensaje": "Debes seleccionar al menos un producto."
        })

    detalles_no_seleccionados = solicitud.detalles.filter(
        seleccionado=False
    )

    if detalles_no_seleccionados.exists():

        nueva_solicitud = SolicitudCotizacion.objects.create(
            usuario=request.user,
            enviada=True,
            estado="revision"
        )

        for detalle in detalles_seleccionados:

            DetalleSolicitud.objects.create(
                solicitud=nueva_solicitud,
                producto=detalle.producto,
                cantidad=detalle.cantidad,
                seleccionado=True
            )

        detalles_seleccionados.delete()

        solicitud.detalles.update(
            seleccionado=True
        )

    else:

        solicitud.enviada = True
        solicitud.estado = "revision"
        solicitud.save()

        nueva_solicitud = solicitud

    request.session.pop("solicitud_editando_id", None)

    return JsonResponse({
        "ok": True,
        "solicitud_id": nueva_solicitud.id
    })

@login_required
def mis_cotizaciones(request):

    solicitudes = SolicitudCotizacion.objects.filter(
        usuario=request.user,
        enviada=True
    ).order_by("-fecha")

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

    negro = colors.HexColor("#111827")
    dorado = colors.HexColor("#C9A227")
    gris = colors.HexColor("#6B7280")
    gris_claro = colors.HexColor("#F8F9FA")
    borde = colors.HexColor("#E5E7EB")

    # =====================================================
    # LOGO
    # =====================================================

    logo_path = os.path.join(
        settings.BASE_DIR,
        "static",
        "img",
        "logo_cooperativa.png"
    )

    if os.path.exists(logo_path):

        pdf.drawImage(
            logo_path,
            45,
            height - 105,
            width=78,
            height=78,
            preserveAspectRatio=True,
            mask='auto'
        )

    # =====================================================
    # EMPRESA
    # =====================================================

    pdf.setFillColor(negro)

    pdf.setFont("Helvetica-Bold", 17)

    pdf.drawString(
        145,
        height - 48,
        "Comercializadora Cooperativa"
    )

    pdf.setFont("Helvetica-Bold", 11)

    pdf.drawString(
        145,
        height - 67,
        "de Sustancias Químicas para uso del"
    )

    pdf.drawString(
        145,
        height - 82,
        "Artesano Pirotécnico S.A. de C.V."
    )

    pdf.setFillColor(gris)

    pdf.setFont("Helvetica",9)

    pdf.drawString(
        145,
        height - 100,
        "Venta de sustancias químicas • Artificios pirotécnicos"
    )

    # =====================================================
    # LINEA DORADA
    # =====================================================

    pdf.setStrokeColor(dorado)

    pdf.setLineWidth(2)

    pdf.line(
        40,
        height-122,
        width-40,
        height-122
    )

    # =====================================================
    # TITULO
    # =====================================================

    y = height - 165

    pdf.setFillColor(negro)

    pdf.setFont(
        "Helvetica-Bold",
        24
    )

    pdf.drawString(
        40,
        y,
        "COTIZACIÓN"
    )

    pdf.setFillColor(dorado)

    pdf.roundRect(
        width-180,
        y-6,
        140,
        28,
        12,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(colors.white)

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawCentredString(
        width-110,
        y+2,
        f"FOLIO #{solicitud.id}"
    )

    # =====================================================
    # DATOS CLIENTE
    # =====================================================

    y -= 50

    nombre = (
        solicitud.usuario.get_full_name()
        or
        solicitud.usuario.email
    )

    pdf.setFillColor(negro)

    pdf.setFont(
        "Helvetica-Bold",
        10
    )

    pdf.drawString(
        40,
        y,
        "Cliente:"
    )

    pdf.drawString(
        40,
        y-18,
        "Correo:"
    )

    pdf.drawString(
        40,
        y-36,
        "Fecha:"
    )

    pdf.setFillColor(gris)

    pdf.setFont(
        "Helvetica",
        10
    )

    pdf.drawString(
        95,
        y,
        nombre
    )

    pdf.drawString(
        95,
        y-18,
        solicitud.usuario.email
    )

    pdf.drawString(
        95,
        y-36,
        solicitud.fecha.strftime("%d/%m/%Y")
    )

    # =====================================================
    # TABLA
    # =====================================================

    y -= 75

    pdf.setFillColor(gris_claro)

    pdf.roundRect(
        35,
        y,
        540,
        28,
        8,
        fill=1,
        stroke=0
    )

    pdf.setStrokeColor(borde)

    pdf.roundRect(
        35,
        y,
        540,
        28,
        8,
        fill=0,
        stroke=1
    )

    pdf.setFillColor(negro)

    pdf.setFont(
        "Helvetica-Bold",
        10
    )

    pdf.drawString(50, y+9, "Producto")
    pdf.drawString(310, y+9, "Cantidad")
    pdf.drawString(395, y+9, "Precio")
    pdf.drawString(485, y+9, "Subtotal")

    y -= 24

    total = 0

    pdf.setFont(
        "Helvetica",
        10
    )

    for index, detalle in enumerate(solicitud.detalles.all()):

        precio = float(detalle.precio_aplicado or 0)
        subtotal = precio * detalle.cantidad
        total += subtotal

        if index % 2 == 0:
            pdf.setFillColor(colors.white)
        else:
            pdf.setFillColor(gris_claro)

        pdf.roundRect(
            35,
            y - 4,
            540,
            24,
            6,
            fill=1,
            stroke=0
        )

        pdf.setFillColor(negro)

        pdf.drawString(
            50,
            y + 4,
            detalle.producto.nombre[:42]
        )

        pdf.drawCentredString(
            335,
            y + 4,
            str(detalle.cantidad)
        )

        pdf.drawRightString(
            445,
            y + 4,
            f"${precio:,.2f}"
        )

        pdf.drawRightString(
            560,
            y + 4,
            f"${subtotal:,.2f}"
        )

        y -= 26

        if y < 155:
            pdf.showPage()
            y = height - 80

    # =====================================================
    # TOTAL
    # =====================================================

    y -= 20

    pdf.setFillColor(dorado)

    pdf.roundRect(
        360,
        y - 12,
        215,
        42,
        14,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(colors.white)

    pdf.setFont(
        "Helvetica-Bold",
        14
    )

    pdf.drawRightString(
        558,
        y + 3,
        f"TOTAL: ${total:,.2f}"
    )

    # =====================================================
    # OBSERVACIONES
    # =====================================================

    y -= 70

    pdf.setFillColor(negro)

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    pdf.drawString(
        40,
        y,
        "Observaciones"
    )

    pdf.setFillColor(gris)

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.drawString(
        40,
        y - 20,
        "• Cotización válida por 15 días naturales."
    )

    pdf.drawString(
        40,
        y - 36,
        "• Precios sujetos a cambios sin previo aviso."
    )

    pdf.drawString(
        40,
        y - 52,
        "• Para continuar con el proceso, comunícate con la cooperativa."
    )

    # =====================================================
    # PIE DE PÁGINA
    # =====================================================

    pdf.setStrokeColor(dorado)

    pdf.setLineWidth(1.5)

    pdf.line(
        40,
        72,
        width - 40,
        72
    )

    pdf.setFillColor(negro)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        40,
        52,
        "Comercializadora Cooperativa de Sustancias Químicas para uso del Artesano Pirotécnico, S.A. de C.V."
    )

    pdf.setFillColor(gris)

    pdf.setFont(
        "Helvetica",
        8
    )

    pdf.drawString(
        40,
        38,
        "San Mateo Tlalchichilpan, Almoloya de Juárez, Estado de México, C.P. 50904"
    )

    pdf.drawRightString(
        width - 40,
        38,
        "Tel. 725 136 07 31"
    )

    pdf.drawRightString(
        width - 40,
        24,
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
        usuario=request.user,
        enviada=True,
        estado="revision"
    )

    solicitud.enviada = False
    solicitud.save()

    request.session["solicitud_editando_id"] = solicitud.id

    messages.success(
        request,
        "Tu solicitud volvió a edición. Puedes modificarla y enviarla nuevamente."
    )

    return redirect("solicitudes")


@login_required
def eliminar_solicitud_en_revision(request, id):

    solicitud = get_object_or_404(
        SolicitudCotizacion,
        id=id,
        usuario=request.user,
        enviada=True,
        estado="revision"
    )

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

    solicitud.enviada = True
    solicitud.save()

    request.session.pop("solicitud_editando_id", None)

    messages.info(
        request,
        "La edición fue cancelada. La cotización quedó en revisión."
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

        request.user.first_name = request.POST.get("first_name")
        request.user.email = request.POST.get("email")
        request.user.save()

        perfil.telefono = request.POST.get("telefono")
        perfil.municipio = request.POST.get("municipio")
        perfil.estado = request.POST.get("estado")

        if request.FILES.get("foto"):
            perfil.foto = request.FILES.get("foto")

        perfil.save()

        messages.success(request, "Perfil actualizado correctamente.")
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