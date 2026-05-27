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

]