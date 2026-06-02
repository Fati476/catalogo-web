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

    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT
    )

    estado = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    destacado = models.BooleanField(
        default=False,
        verbose_name="Producto destacado"
    )


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
    

class SolicitudCotizacion(models.Model):

    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('Revisada', 'Revisada'),
        ('Cotizada', 'Cotizada'),
        ('Rechazada', 'Rechazada'),
    ]

    cliente = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='Pendiente'
    )

    comentario = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):

        return f"Solicitud #{self.id}"
    

class DetalleSolicitud(models.Model):

    solicitud = models.ForeignKey(
        SolicitudCotizacion,
        on_delete=models.CASCADE,
        related_name='detalles'
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE
    )

    cantidad = models.PositiveIntegerField(
        default=1
    )

    def __str__(self):

        return self.producto.nombre