from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required

from catalogo_web import settings
from sistema.utils import enviar_correo
from .forms import RegistroForm
from .models import Producto, Perfil


@login_required
def inicio(request):

    productos = Producto.objects.all()

    return render(request, 'sistema/inicio.html', {
        'productos': productos
    })


def registro(request):

    if request.method == 'POST':

        form = RegistroForm(request.POST)

        if form.is_valid():

            usuario = form.save()

            municipio = request.POST.get('municipio')
            estado = request.POST.get('estado')

            Perfil.objects.create(
                usuario=usuario,
                municipio=municipio,
                estado=estado
            )

            return redirect('/accounts/login/')

        else:

            print(form.errors)

    else:

        form = RegistroForm()

    return render(request, 'registration/registro.html', {
        'form': form
    })

