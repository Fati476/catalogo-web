from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group

from .forms import RegistroForm
from .models import Producto, Perfil

from .forms_producto import ProductoForm
from .models import Producto

from .forms_categoria import CategoriaForm
from .models import Categoria


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

    return render(request, 'admin/panel_admin.html')

@login_required
def lista_productos(request):

    productos = Producto.objects.all()

    return render(request, 'admin/productos/lista.html', {
        'productos': productos
    })


@login_required
def agregar_producto(request):

    if request.method == 'POST':

        form = ProductoForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect('lista_productos')

    else:

        form = ProductoForm()

    return render(request, 'admin/productos/agregar.html', {
        'form': form
    })


@login_required
def lista_categorias(request):

    categorias = Categoria.objects.all()

    return render(request,
                  'panel/categorias/lista.html',
                  {
                      'categorias': categorias
                  })


@login_required
def agregar_categoria(request):

    if request.method == 'POST':

        form = CategoriaForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect('lista_categorias')

    else:

        form = CategoriaForm()

    return render(request,
                  'panel/categorias/agregar.html',
                  {
                      'form': form
                  })