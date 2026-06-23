from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings


def enviar_correo_prueba(destinatario):
    mensaje = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=destinatario,
        subject="Prueba de SendGrid",
        html_content="""
        <h2>Hola</h2>
        <p>Este es un correo de prueba enviado desde tu sistema de cotizaciones.</p>
        """
    )

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    sg.send(mensaje)