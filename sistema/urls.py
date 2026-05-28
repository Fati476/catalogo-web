from django.urls import path
from . import views

urlpatterns = [

    path('', views.inicio, name='inicio'),

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
        'panel/categorias/',
        views.lista_categorias,
        name='lista_categorias'
    ),

    path(
        'panel/categorias/agregar/',
        views.agregar_categoria,
        name='agregar_categoria'
    ),

]