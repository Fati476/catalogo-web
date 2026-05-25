from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
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

    enviar_correo(
        'fm2290759@gmail.com',
        'Prueba SendGrid',
        '<h1>YA FUNCIONA 😭</h1>'
    )

    return HttpResponse("Correo enviado")