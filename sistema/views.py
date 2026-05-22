from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from .forms import RegistroForm
from .models import Producto


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

            grupo = Group.objects.get(name='Cliente')

            usuario.groups.add(grupo)

            return redirect('login')

    else:

        form = RegistroForm()

    return render(request, 'registration/registro.html', {
        'form': form
    })