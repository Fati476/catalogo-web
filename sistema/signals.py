
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from .models import RegistroActividad


@receiver(user_logged_in)
def registrar_inicio_sesion(sender, request, user, **kwargs):
    RegistroActividad.objects.create(
        usuario=user,
        accion='Inicio de sesión',
        descripcion='El usuario inició sesión correctamente.'
    )



@receiver(user_login_failed)
def registrar_intento_fallido(sender, credentials, request, **kwargs):
    identificador = credentials.get('username', 'No identificado')

    RegistroActividad.objects.create(
        usuario=None,
        accion='Inicio de sesión fallido',
        descripcion=(
            f'Credenciales incorrectas. '
            f'Identificador utilizado: {identificador}'
        )
    )

