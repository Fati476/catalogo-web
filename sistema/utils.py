from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings


def enviar_correo(destinatario, asunto, contenido):

    mensaje = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=destinatario,
        subject=asunto,
        html_content=contenido
    )

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

        response = sg.send(mensaje)

        print(response.status_code)

        return True

    except Exception as e:
        print("ERROR:", e)
        return False