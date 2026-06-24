
import base64

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail,
    Attachment,
    FileContent,
    FileName,
    FileType,
    Disposition,
)

from django.conf import settings


def enviar_cotizacion(destinatario, pdf_bytes, numero_cotizacion):

    mensaje = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=destinatario,
        subject=f"Cotización #{numero_cotizacion} - Cooperativa Pirotécnica",
        html_content=f"""
        <h2>Estimado cliente:</h2>

        <p>
            Su cotización <strong>#{numero_cotizacion}</strong> ha sido generada correctamente.
        </p>

        <p>
            En este correo encontrará adjunto el archivo PDF con el detalle de su cotización.
        </p>

        <br>

        <p>
            Agradecemos su preferencia.
        </p>

        <p>
            <strong>
            Comercializadora Cooperativa de Sustancias Químicas
            para uso del Artesano Pirotécnico S.A. de C.V.
            </strong>
        </p>
        """
    )

    encoded = base64.b64encode(pdf_bytes).decode()

    mensaje.attachment = Attachment(
        FileContent(encoded),
        FileName(f"Cotizacion_{numero_cotizacion}.pdf"),
        FileType("application/pdf"),
        Disposition("attachment"),
    )

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    sg.send(mensaje)
