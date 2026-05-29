from cloudinary.models import CloudinaryField
from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class ProductoImagen(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='imagenes'
    )
    imagen = CloudinaryField('imagen')

    def __str__(self):
        return self.producto.nombre
    

class Perfil(models.Model):

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)

    municipio = models.CharField(max_length=100)

    estado = models.CharField(max_length=100)
    telefono = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.usuario.username