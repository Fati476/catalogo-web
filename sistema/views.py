from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required

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

            grupo = Group.objects.get(name='Cliente')

            usuario.groups.add(grupo)

            return redirect('login')

    else:

        form = RegistroForm()

    return render(request, 'registration/registro.html', {
        'form': form
    })


def prueba(request):

    enviado = enviar_correo(
        "fm2290759@gmail.com",
        "Prueba SendGrid",
        "<h1>Hola desde Django</h1>"
    )

    if enviado:
        return HttpResponse("Correo enviado")
    else:
        return HttpResponse("Error enviando correo")