from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

from django.contrib.auth.models import User
urlpatterns = [

    path(
        '',
        auth_views.LoginView.as_view(),
        name='login'
    ),

    path('registro/', views.registro, name='registro'),

    path(
        'redireccion/',
        views.redireccion_inicio,
        name='redireccion'
    ),

    path(
        'panel-admin/',
        views.panel_admin,
        name='panel_admin'
    ),

    path(
        'inicio/',
        views.inicio,
        name='inicio'
    ),

    # CATEGORIAS

    path(
        'panel/categorias/',
        views.lista_categorias,
        name='lista_categorias'
    ),

    path(
        'panel/categorias/agregar/',
        views.agregar_categoria,
        name='agregar_categoria'
    ),


    path(
        'panel/categorias/editar/<int:id>/',
        views.editar_categoria,
        name='editar_categoria'
    ),

    path(
        'panel/categorias/eliminar/<int:id>/',
        views.eliminar_categoria,
        name='eliminar_categoria'
    ),

    path('categoria/<int:id>/', views.productos_por_categoria, name='productos_categoria'),

    # PRODUCTOS

    path(
        'panel/productos/',
        views.lista_productos,
        name='lista_productos'
    ),

    path(
        'panel/productos/agregar/',
        views.agregar_producto,
        name='agregar_producto'
    ),

    path(
        'panel/productos/eliminar/<int:id>/',
        views.eliminar_producto,
        name='eliminar_producto'
    ),

    path(
        'panel/productos/editar/<int:id>/',
        views.editar_producto,
        name='editar_producto'
    ),


    path(
        'panel/productos/imagen/eliminar/<int:id>/',
        views.eliminar_imagen,
        name='eliminar_imagen'
    ),

    path(
        'favorito/<int:producto_id>/',
        views.toggle_favorito,
        name='toggle_favorito'
    ),

    #DASHBOARD

    path(
        'dashboard/',
        views.dashboard,
        name='dashboard'
    ),

    # USUARIOS

    path(
        'panel/usuarios/',
        views.lista_usuarios,
        name='lista_usuarios'
    ),

    path(
        'panel/usuarios/estado/<int:id>/',
        views.cambiar_estado_usuario,
        name='cambiar_estado_usuario'
    ),


    path(
        'panel/usuarios/estado/<int:id>/',
        views.cambiar_estado_usuario,
        name='cambiar_estado_usuario'
    ),

    

    #Cotizaciones
    path(
        'panel/solicitudes/',
        views.lista_solicitudes,
        name='lista_solicitudes'
    ),


    path('favorito/<int:producto_id>/', views.toggle_favorito, name='toggle_favorito'),

    path('cotizar/<int:producto_id>/', views.agregar_cotizacion, name='agregar_cotizacion'),

    path('categorias/', views.todas_categorias, name='todas_categorias'),


    #Todos los produtos 
    path(
        'productos/',
        views.todos_productos,
        name='todos_productos'
    ),

    path(
        'favoritos/',
        views.favoritos,
        name='favoritos'
    ),

    path(
        'solicitudes/',
        views.solicitudes,
        name='solicitudes'
    ),


    path(
        'solicitud/eliminar/<int:id>/',
        views.eliminar_detalle,
        name='eliminar_detalle'
    ),

    path(
        'solicitud/aumentar/<int:id>/',
        views.aumentar_cantidad,
        name='aumentar_cantidad'
    ),

    path(
        'solicitud/disminuir/<int:id>/',
        views.disminuir_cantidad,
        name='disminuir_cantidad'
    ),

]