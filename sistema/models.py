from cloudinary.models import CloudinaryField
from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()

    imagen = CloudinaryField(
        "imagen",
        null=True,
        blank=True
    )

    def __str__(self):
        return self.nombre

class Producto(models.Model):

    nombre = models.CharField(max_length=100)

    descripcion = models.TextField()

    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT
    )

    estado = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

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

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    telefono = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    municipio = models.CharField(
        max_length=100,
        blank=True
    )

    estado = models.CharField(
        max_length=100,
        blank=True
    )

    foto = CloudinaryField(
        "foto",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.usuario.username
    
  
    

class Favorito(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('usuario', 'producto')


class SolicitudCotizacion(models.Model):

    ESTADOS = [
        ("revision", "En revisión"),
        ("cotizada", "Cotizada"),
        ("rechazada", "Rechazada"),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    enviada = models.BooleanField(
        default=False
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="revision"
    )

    numero_usuario = models.PositiveIntegerField(
        null=True,
        blank=True,
        editable=False
    )

    # Impide que el cliente edite mientras el administrador la procesa
    bloqueada = models.BooleanField(
        default=False
    )

    pdf = models.FileField(
        upload_to="cotizaciones/",
        blank=True,
        null=True
    )

    motivo_rechazo = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"Solicitud #{self.id}"


class DetalleSolicitud(models.Model):

    DISPONIBILIDADES = [
        ("disponible", "Disponible"),
        ("no_disponible", "Temporalmente no disponible"),
        ("descontinuado", "Producto descontinuado"),
    ]

    solicitud = models.ForeignKey(
        SolicitudCotizacion,
        on_delete=models.CASCADE,
        related_name="detalles"
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE
    )

    cantidad = models.PositiveIntegerField(
        default=1
    )

    seleccionado = models.BooleanField(
        default=True
    )

    precio_aplicado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    disponibilidad = models.CharField(
        max_length=20,
        choices=DISPONIBILIDADES,
        default="disponible"
    )

    observacion_disponibilidad = models.CharField(
        max_length=250,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.producto.nombre