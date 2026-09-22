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


from .models import ProductoImagen

from django.contrib import messages

from django.db.models import Count, Max

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

        solicitud.detalles.update(
            seleccionado=True
        )

    else:

        solicitud.enviada = True
        solicitud.estado = "revision"
        solicitud.bloqueada = False
        solicitud.numero_usuario = numero_usuario

        solicitud.save(
            update_fields=[
                "enviada",
                "estado",
                "bloqueada",
                "numero_usuario"
            ]
        )

        nueva_solicitud = solicitud

    request.session.pop(
        "solicitud_editando_id",
        None
    )

    request.session.pop(
        "piroia_solicitud_id",
        None
    )

    messages.success(
        request,
        "Tu solicitud fue enviada correctamente. Puedes consultar su estado aquí."
    )

    return JsonResponse({
        "ok": True,
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

    # Si es una solicitud antigua y todavía no tiene número,
    # se le asigna uno antes de comenzar la edición.
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

    # Si la solicitud fue creada por PiroIA,
    # se elimina completamente porque todavía es un borrador.
    if request.session.get("piroia_solicitud_id") == solicitud.id:

        solicitud.delete()

        request.session.pop(
            "piroia_solicitud_id",
            None
        )

        request.session.pop(
            "solicitud_editando_id",
            None
        )

        messages.info(
            request,
            "La solicitud creada por PiroIA fue cancelada."
        )

        return redirect("solicitudes")

    # ----------------------------------------------------------
    # EDICIÓN NORMAL DE UNA SOLICITUD YA ENVIADA
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
@require_POST
def chatbot_ia(request):
    """
    PiroIA:
    - Consulta el catálogo
    - Crea solicitudes de cotización
    - Modifica solicitudes mediante lenguaje natural
    - Funciona con texto y voz desde el frontend
    """

    try:
        data = json.loads(request.body)

        pregunta = data.get("mensaje", "").strip()
        modo = data.get("modo", "consulta").strip().lower()

        # Historial reciente enviado por el frontend.
        # Sirve para que PiroIA entienda referencias como
        # "tres de cada una", "sí por favor", "quita uno", etc.
        historial = data.get("historial", [])

        if not isinstance(historial, list):
            historial = []

        # Solo usamos las últimas 12 intervenciones para no hacer
        # crecer demasiado el contexto enviado a OpenRouter.
        historial_reciente = historial[-12:]

        if not pregunta:
            return JsonResponse({
                "ok": False,
                "respuesta": "Escribe o di algo para que pueda ayudarte."
            })

        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            return JsonResponse({
                "ok": False,
                "respuesta": "No se encontró la configuración de PiroIA."
            }, status=500)

        # ==========================================================
        # 1. OBTENER CATÁLOGO REAL
        # ==========================================================

        productos_catalogo = (
            Producto.objects
            .filter(estado=True)
            .select_related("categoria")
            .prefetch_related("imagenes")
        )

        catalogo = []

        for producto in productos_catalogo:

            imagen_url = ""

            try:
                primera_imagen = producto.imagenes.first()

                if primera_imagen and primera_imagen.imagen:
                    imagen_url = primera_imagen.imagen.url

            except Exception:
                imagen_url = ""

            # IMPORTANTE:
            # El ID se conserva solamente para uso interno del sistema.
            # El precio NO se manda a PiroIA.
            catalogo.append({
                "id": producto.id,
                "nombre": producto.nombre,
                "descripcion": producto.descripcion or "",
                "categoria": (
                    producto.categoria.nombre
                    if producto.categoria
                    else ""
                ),
                "imagen": imagen_url,
            })

        # ==========================================================
        # 2. SOLICITUD ACTIVA DE PIROIA
        # ==========================================================

        solicitud_id = (
            request.session.get("piroia_solicitud_id")
            or request.session.get("solicitud_editando_id")
        )

        solicitud_actual = None

        if solicitud_id:
            solicitud_actual = SolicitudCotizacion.objects.filter(
                id=solicitud_id,
                usuario=request.user,
                enviada=False,
                estado="revision",
                bloqueada=False
            ).first()

            # Si la solicitud guardada en sesión ya fue enviada,
            # cancelada o bloqueada, dejamos de considerarla activa.
            if solicitud_actual is None:
                request.session.pop("piroia_solicitud_id", None)

        productos_solicitud = []

        if solicitud_actual:
            detalles = solicitud_actual.detalles.select_related(
                "producto"
            ).all()

            for detalle in detalles:
                productos_solicitud.append({
                    "id": detalle.producto.id,
                    "nombre": detalle.producto.nombre,
                    "cantidad": detalle.cantidad,
                })

        # ==========================================================
        # 3. INFORMACIÓN PARA LA IA
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
        # 4. REGLAS GENERALES DE PIROIA
        # ==========================================================

        reglas_piroia = """
REGLAS OBLIGATORIAS DE RESPUESTA:

- Nunca muestres IDs, identificadores internos o números internos
  de productos.
- Nunca muestres precios, costos, importes ni cantidades monetarias.
- El precio de todos los productos se determina mediante cotización.
- Si el usuario pregunta por un precio, responde exactamente con una
  idea como:
  "El precio de los productos se determina mediante cotización.
  Si deseas, puedo ayudarte a preparar una solicitud con la cantidad
  que necesitas."
- Cuando hables de cantidades utiliza siempre "pieza" o "piezas".
- Ejemplo correcto:
  "Agregué 3 piezas de Pachanga Plus."
- Ejemplo incorrecto:
  "Agregué el ID 33 cantidad 3."
- Los IDs solamente sirven internamente para que el sistema encuentre
  los productos.
- Nunca menciones esos IDs al usuario.
- No inventes productos.
- No inventes cantidades.
- Responde siempre en español.
- Sé claro, natural y breve.
"""

        # ==========================================================
        # 5. PROMPT DE PIROIA
        # ==========================================================

        if modo == "solicitud":

            instrucciones = f"""
Eres PiroIA, el asistente inteligente del catálogo web de una
cooperativa de productos pirotécnicos.

Tu función es ayudar EXCLUSIVAMENTE con el catálogo y las
solicitudes de cotización.

{reglas_piroia}

NO proporciones instrucciones para fabricar, modificar, combinar,
manipular, encender o utilizar productos pirotécnicos.

Tu trabajo es interpretar lo que el usuario quiere solicitar
y relacionarlo con los productos reales del catálogo.

CATÁLOGO REAL:

{catalogo_texto}

SOLICITUD ACTUAL DEL USUARIO:

{solicitud_texto}

CONVERSACIÓN RECIENTE:

{historial_texto}

IMPORTANTE SOBRE EL CONTEXTO DE LA CONVERSACIÓN:

- Utiliza la conversación reciente para entender referencias como
  "cada una", "los dos", "ese producto", "agrega otro", "quita uno",
  "sí", "sí por favor", "créala", "esa está bien" y expresiones similares.
- Nunca trates el mensaje actual como una conversación aislada.
- Si el usuario dice "tres de cada una", identifica los productos
  mencionados inmediatamente antes en la conversación.
- Si el usuario dice "sí", "sí por favor", "confirmo" o una expresión
  equivalente, utiliza la solicitud que se acaba de construir en la
  conversación para determinar qué debe confirmarse.
- Si existe una solicitud activa, trabaja siempre sobre ESA solicitud.
- No cambies automáticamente a otra solicitud.
- La solicitud activa permanece vigente hasta que el usuario la envíe
  o la cancele.
- El historial de conversación sirve para interpretar la intención,
  pero la información real de productos y cantidades debe validarse
  contra la solicitud y el catálogo.

REGLA ESPECIAL PARA CONVERSACIONES DE SOLICITUD:

- Si el usuario primero menciona un producto y después indica solamente
  una cantidad, relaciona esa cantidad con el producto mencionado.
- Por ejemplo, si el usuario dijo "Pachanga Plus" y después dice
  "quiero tres unidades", debes interpretar "tres unidades" como
  "3 piezas de Pachanga Plus".
- Cuando ya tengas producto + cantidad, NO pidas nuevamente el nombre
  del producto.
- En ese caso devuelve accion="agregar" y el producto con la cantidad
  correspondiente.
- La primera indicación de producto + cantidad prepara el borrador.
- Después de preparar el borrador, el sistema preguntará si desea
  agregar o modificar algo.
- Si el usuario responde "no", "no quiero modificaciones",
  "así está bien", "está bien", "eso es todo", "déjalo así" o una
  expresión equivalente, devuelve confirmado=true.
- Si el usuario responde que sí quiere modificar, NO confirmes todavía:
  continúa trabajando sobre la misma solicitud activa.

Si el usuario quiere crear una solicitud nueva, identifica los
productos del catálogo y las cantidades.

Si el usuario quiere agregar un producto, quitarlo o cambiar su
cantidad, identifica correctamente el producto.

IMPORTANTE:

- Solo puedes utilizar productos que existan en el catálogo.
- No inventes productos.
- No inventes IDs.
- No inventes cantidades que el usuario no haya indicado.
- Si no estás seguro del producto, pide aclaración.
- No envíes automáticamente la solicitud.
- El usuario debe revisar la solicitud y presionar el botón
  "Enviar solicitud".
- Nunca menciones el ID del producto.
- Nunca menciones el precio.
- Nunca menciones información interna del sistema.

Cuando respondas sobre una cantidad, utiliza:

1 pieza

o:

5 piezas

Nunca escribas solamente:

"cantidad 5"

Nunca escribas:

"ID 33 cantidad 5"

Cuando confirmes una solicitud, menciona el nombre del producto
y su cantidad.

Ejemplo:

"Perfecto. Tu solicitud quedó preparada con 3 piezas de Pachanga Plus.
Los precios se determinarán mediante cotización."

Debes responder ÚNICAMENTE con JSON válido usando exactamente
esta estructura:

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

REGLAS DE ACCIONES:

1. "agregar":
   Se utiliza cuando el usuario quiere agregar productos.

2. "quitar":
   Se utiliza cuando el usuario quiere eliminar un producto o
   disminuir su cantidad.

3. "cambiar":
   Se utiliza cuando el usuario quiere establecer una cantidad
   diferente.

4. "ninguna":
   Se utiliza cuando solamente está preguntando algo,
   necesita aclaración o todavía no ha confirmado.

5. "confirmado" debe ser true SOLO cuando el usuario confirme
   claramente que desea crear o actualizar la solicitud.

6. Si el mensaje actual es una confirmación breve como "sí",
   "sí por favor", "confirmo", "esa está bien", "créala" o
   "ya quedó", revisa la conversación reciente para recuperar
   los productos y cantidades que se estaban confirmando.

7. Si en la conversación reciente el usuario ya indicó cantidades
   concretas y después confirma, conserva esas cantidades.

Si el usuario dice:

"quiero 2 cajas de X y 3 de Y"

puedes preparar la solicitud.

Si dice:

"sí, créala"
"confirmo"
"esa está bien"
"crear solicitud"
"ya quedó"
"eso es todo"

entonces "confirmado" debe ser true.

Si ya existe una solicitud activa, las acciones deben aplicarse
sobre esa solicitud.

Pregunta del usuario:

{pregunta}
"""

        else:

            instrucciones = f"""
Eres PiroIA, el asistente inteligente del catálogo web.

Tu función en este modo es CONSULTAR el catálogo.

{reglas_piroia}

CATÁLOGO REAL:

{catalogo_texto}

Responde de forma clara y sencilla utilizando solamente la
información disponible en el catálogo.

Puedes informar sobre:

- productos
- descripciones
- categorías
- características descritas en el catálogo
- disponibilidad de productos en el catálogo

NO proporciones instrucciones para fabricar, modificar, combinar,
manipular, encender o utilizar productos pirotécnicos.

Si el usuario pregunta por el precio o costo de un producto,
NO proporciones ninguna cantidad monetaria.

Responde:

"El precio de los productos se determina mediante cotización.
Si deseas, puedo ayudarte a preparar una solicitud con la cantidad
que necesitas."

Si el producto que busca el usuario no existe en el catálogo,
indícalo claramente.

Nunca muestres IDs ni identificadores internos.

Pregunta del usuario:

{pregunta}
"""

        # ==========================================================
        # 6. LLAMADA A OPENROUTER
        # ==========================================================

        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://catalogo-web-s5um.onrender.com",
            "X-Title": "PiroIA - Catalogo Web",
        }

        payload = {
            "model": "openrouter/free",
            "messages": [
                {
                    "role": "user",
                    "content": instrucciones
                }
            ],
            "temperature": 0.2,
            "max_tokens": 1500
        }

        print("====================================")
        print("PIROIA - OPENROUTER")
        print("Pregunta:", pregunta)
        print("Modo:", modo)
        print("API KEY:", "SI" if api_key else "NO")
        print("====================================")

        try:
            respuesta_ia = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=20
            )

        except requests.exceptions.Timeout:

            print("OPENROUTER TIMEOUT")

            return JsonResponse({
                "ok": False,
                "respuesta": (
                    "PiroIA tardó demasiado en responder. "
                    "Intenta nuevamente."
                ),
                "gemini_timeout": False
            })

        except requests.exceptions.RequestException as e:

            print(
                "ERROR DE CONEXIÓN OPENROUTER:",
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
            "STATUS OPENROUTER:",
            respuesta_ia.status_code
        )

        print(
            "RESPUESTA OPENROUTER:",
            respuesta_ia.text[:2000]
        )

        # ==========================================================
        # 7. ERROR DE OPENROUTER
        # ==========================================================

        if respuesta_ia.status_code != 200:

            try:
                error_data = respuesta_ia.json()

                error_mensaje = (
                    error_data.get("error", {}).get("message")
                    or "Error desconocido de OpenRouter."
                )

            except Exception:

                error_mensaje = (
                    "OpenRouter no pudo procesar la solicitud."
                )

            return JsonResponse({
                "ok": False,
                "respuesta": (
                    f"PiroIA no pudo responder: "
                    f"{error_mensaje}"
                )
            })

        # ==========================================================
        # 8. EXTRAER RESPUESTA
        # ==========================================================

        try:

            resultado = respuesta_ia.json()

            contenido = (
                resultado.get("choices", [{}])[0]
                .get("message", {})
                .get("content")
            )

            if contenido is None:

                print("OPENROUTER DEVOLVIÓ CONTENT = NONE")

                razon = (
                    resultado.get("choices", [{}])[0]
                    .get("finish_reason")
                )

                print("FINISH REASON:", razon)

                return JsonResponse({
                    "ok": True,
                    "respuesta": (
                        "PiroIA necesitó más tiempo para interpretar "
                        "la solicitud. Intenta nuevamente de forma breve."
                    ),
                    "confirmado": False,
                    "accion": "ninguna",
                    "productos": []
                })

        except Exception as e:

            print(
                "ERROR LEYENDO RESPUESTA:",
                str(e)
            )

            return JsonResponse({
                "ok": False,
                "respuesta": (
                    "PiroIA recibió una respuesta "
                    "que no pudo interpretar."
                )
            })

        contenido = str(contenido).strip()

        if not contenido:

            return JsonResponse({
                "ok": True,
                "respuesta": (
                    "No pude interpretar la respuesta de PiroIA. "
                    "Intenta nuevamente."
                ),
                "confirmado": False,
                "accion": "ninguna",
                "productos": []
            })

        # ==========================================================
        # 9. MODO CONSULTA
        # ==========================================================

        if modo != "solicitud":

            # Protección adicional:
            # nunca devolver al frontend una respuesta que contenga
            # información monetaria o identificadores internos.

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

            pregunta_lower = pregunta.lower()

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
                "respuesta": (
                    "Necesito un poco más de información para "
                    "entender tu solicitud. ¿Qué producto y cuántas "
                    "piezas necesitas?"
                ),
                "confirmado": False,
                "accion": "ninguna",
                "productos": []
            })

        # ==========================================================
        # 10. INTERPRETAR JSON DE LA IA
        # ==========================================================

        contenido_json = contenido

        if contenido_json.startswith("```"):

            contenido_json = contenido_json.replace(
                "```json",
                ""
            )

            contenido_json = contenido_json.replace(
                "```",
                ""
            )

            contenido_json = contenido_json.strip()

        try:

            resultado_ia = json.loads(
                contenido_json
            )

        except json.JSONDecodeError:

            print(
                "LA IA NO DEVOLVIÓ JSON VÁLIDO:"
            )

            print(contenido)

            return JsonResponse({
                "ok": True,
                "respuesta": contenido,
                "confirmado": False,
                "accion": "ninguna",
                "productos": []
            })

        respuesta_texto = resultado_ia.get(
            "respuesta",
            "Puedo ayudarte a preparar la solicitud."
        )

        accion = resultado_ia.get(
            "accion",
            "ninguna"
        )

        confirmado = resultado_ia.get(
            "confirmado",
            False
        )

        productos = resultado_ia.get(
            "productos",
            []
        )

        # ==========================================================
        # 11. PROTECCIÓN CONTRA PRECIOS
        # ==========================================================

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

        if any(
            palabra in pregunta.lower()
            for palabra in palabras_precio
        ):

            respuesta_texto = (
                "El precio de los productos se determina "
                "mediante cotización. Si deseas, puedo ayudarte "
                "a preparar una solicitud con la cantidad "
                "que necesitas."
            )

            return JsonResponse({
                "ok": True,
                "respuesta": respuesta_texto,
                "confirmado": False,
                "accion": "ninguna",
                "productos": []
            })

        # ==========================================================
        # 12. CREAR SOLICITUD NUEVA
        # ==========================================================

        if (accion in ["agregar", "quitar", "cambiar"]
                and productos
                and not solicitud_actual):

            solicitud_actual = SolicitudCotizacion.objects.create(
                usuario=request.user,
                enviada=False,
                estado="revision",
                bloqueada=False
            )

            request.session[
                "piroia_solicitud_id"
            ] = solicitud_actual.id

            # Conservamos esta solicitud como la única solicitud
            # activa de PiroIA hasta que se envíe o cancele.
            request.session.modified = True

            solicitud_id = solicitud_actual.id

        # ==========================================================
        # 13. MODIFICAR SOLICITUD
        # ==========================================================

        cambios_realizados = []

        if solicitud_actual and accion in [
            "agregar",
            "quitar",
            "cambiar"
        ]:

            for item in productos:

                try:

                    producto_id = int(
                        item.get("producto_id")
                    )

                    cantidad = int(
                        item.get("cantidad", 1)
                    )

                except (TypeError, ValueError):

                    continue

                if cantidad < 0:
                    continue

                producto = Producto.objects.filter(
                    id=producto_id,
                    estado=True
                ).first()

                if not producto:
                    continue

                detalle = DetalleSolicitud.objects.filter(
                    solicitud=solicitud_actual,
                    producto=producto
                ).first()

                # ==================================================
                # AGREGAR
                # ==================================================

                if accion == "agregar":

                    cantidad_agregada = max(
                        cantidad,
                        1
                    )

                    if detalle:

                        detalle.cantidad += (
                            cantidad_agregada
                        )

                        detalle.seleccionado = True
                        detalle.save()

                    else:

                        DetalleSolicitud.objects.create(
                            solicitud=solicitud_actual,
                            producto=producto,
                            cantidad=cantidad_agregada,
                            seleccionado=True
                        )

                    cantidad_actual = (
                        detalle.cantidad
                        if detalle
                        else cantidad_agregada
                    )

                    unidad = (
                        "pieza"
                        if cantidad_agregada == 1
                        else "piezas"
                    )

                    cambios_realizados.append(
                        f"Agregué {cantidad_agregada} "
                        f"{unidad} de {producto.nombre}. "
                        f"Ahora tienes {cantidad_actual} "
                        f"{'pieza' if cantidad_actual == 1 else 'piezas'}."
                    )

                # ==================================================
                # CAMBIAR
                # ==================================================

                elif accion == "cambiar":

                    if cantidad <= 0:

                        if detalle:
                            detalle.delete()

                        cambios_realizados.append(
                            f"Quité {producto.nombre} "
                            f"de la solicitud."
                        )

                    else:

                        if detalle:

                            detalle.cantidad = cantidad
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
                            f"Cambié {producto.nombre} "
                            f"a {cantidad} "
                            f"{'pieza' if cantidad == 1 else 'piezas'}."
                        )

                # ==================================================
                # QUITAR
                # ==================================================

                elif accion == "quitar":

                    if detalle:

                        if cantidad >= detalle.cantidad:

                            detalle.delete()

                            cambios_realizados.append(
                                f"Quité {producto.nombre} "
                                f"de la solicitud."
                            )

                        else:

                            detalle.cantidad -= cantidad

                            if detalle.cantidad <= 0:

                                detalle.delete()

                                cambios_realizados.append(
                                    f"Quité {producto.nombre} "
                                    f"de la solicitud."
                                )

                            else:

                                detalle.save()

                                cambios_realizados.append(
                                    f"Quité {cantidad} "
                                    f"{'pieza' if cantidad == 1 else 'piezas'} "
                                    f"de {producto.nombre}. "
                                    f"Ahora quedan "
                                    f"{detalle.cantidad} "
                                    f"{'pieza' if detalle.cantidad == 1 else 'piezas'}."
                                )

        # ==========================================================
        # 14. CONFIRMACIÓN FINAL
        # ==========================================================

        if confirmado:

            if solicitud_actual:

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

                        imagen = (
                            detalle.producto.imagenes.first()
                        )

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

                if resumen_productos:

                    respuesta_confirmacion = (
                        "Perfecto. Tu solicitud quedó preparada con "
                        + ", ".join(resumen_productos)
                        + ". Los precios se determinarán mediante "
                          "cotización. No se ha enviado todavía. "
                          "Te llevaré al apartado de Solicitudes para "
                          "que puedas revisarla y, si todo está correcto, "
                          "presiones Enviar solicitud."
                    )

                else:

                    respuesta_confirmacion = (
                        "Tu solicitud no tiene productos. "
                        "Puedes agregar alguno antes de enviarla."
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
        # 15. SOLICITUD PREPARADA, PENDIENTE DE MODIFICACIONES
        # ==========================================================

        if (
            solicitud_actual
            and cambios_realizados
            and not confirmado
            and accion in ["agregar", "quitar", "cambiar"]
        ):

            detalles_preparados = (
                solicitud_actual.detalles
                .select_related("producto")
                .all()
            )

            resumen_preparado = []

            for detalle in detalles_preparados:

                resumen_preparado.append(
                    f"{detalle.cantidad} "
                    f"{'pieza' if detalle.cantidad == 1 else 'piezas'} "
                    f"de {detalle.producto.nombre}"
                )

            if resumen_preparado:

                respuesta_preparada = (
                    "Perfecto. Preparé tu solicitud con "
                    + ", ".join(resumen_preparado)
                    + ". ¿Deseas agregar o modificar algún "
                      "producto o cantidad?"
                )

            else:

                respuesta_preparada = (
                    "La solicitud quedó sin productos. "
                    "¿Deseas agregar algún producto?"
                )

            productos_preparados = []

            for detalle in detalles_preparados:

                productos_preparados.append({
                    "producto_id": detalle.producto.id,
                    "nombre": detalle.producto.nombre,
                    "cantidad": detalle.cantidad
                })

            return JsonResponse({
                "ok": True,
                "respuesta": respuesta_preparada,
                "confirmado": False,
                "accion": accion,
                "productos": productos_preparados
            })

        # ==========================================================
        # 15. RESPUESTA NORMAL DE SOLICITUD
        # ==========================================================

        productos_actualizados = []

        if solicitud_actual:

            detalles_actualizados = (
                solicitud_actual.detalles
                .select_related("producto")
                .all()
            )

            for detalle in detalles_actualizados:

                imagen_url = ""

                try:

                    imagen = (
                        detalle.producto.imagenes.first()
                    )

                    if imagen and imagen.imagen:
                        imagen_url = imagen.imagen.url

                except Exception:

                    imagen_url = ""

                productos_actualizados.append({
                    "producto_id": detalle.producto.id,
                    "nombre": detalle.producto.nombre,
                    "cantidad": detalle.cantidad,
                    "imagen": imagen_url
                })

        # Si el servidor hizo el cambio, usamos nuestro propio
        # mensaje para evitar que la IA diga IDs o precios.

        if cambios_realizados:

            respuesta_texto = " ".join(
                cambios_realizados
            )

        return JsonResponse({
            "ok": True,
            "respuesta": respuesta_texto,
            "confirmado": False,
            "accion": accion,
            "productos": productos_actualizados
        })

    except json.JSONDecodeError:

        return JsonResponse({
            "ok": False,
            "respuesta": (
                "La solicitud enviada no tiene "
                "un formato válido."
            )
        }, status=400)

    except Exception as e:

        print("====================================")
        print("ERROR GENERAL PIROIA")
        print(str(e))
        print("====================================")

        return JsonResponse({
            "ok": False,
            "respuesta": (
                "Ocurrió un problema al procesar "
                "tu solicitud."
            )
        }, status=500)