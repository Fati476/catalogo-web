
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






def enviar_correo_rechazo(destinatario, numero_cotizacion):

    mensaje = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=destinatario,
        subject=f"Solicitud #{numero_cotizacion} - Actualización de estado",
        html_content=f"""
        <h2>Estimado cliente:</h2>

        <p>
            Le informamos que su solicitud de cotización
            <strong>#{numero_cotizacion}</strong>
            fue revisada por nuestro equipo.
        </p>

        <p>
            En esta ocasión no fue posible generar una cotización.
        </p>

        <p>
            Si desea más información o realizar una nueva solicitud,
            estaremos encantados de atenderle.
        </p>

        <br>

        <p>Saludos cordiales.</p>

        <p>
            <strong>
            Comercializadora Cooperativa de Sustancias Químicas
            para uso del Artesano Pirotécnico, S.A. de C.V.
            </strong>
        </p>
        """
    )

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    sg.send(mensaje)



def enviar_bienvenida(usuario):

    mensaje = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=usuario.email,
        subject="Registro exitoso - Catálogo Web",
        html_content=f"""
        <div style="font-family:Arial,sans-serif; max-width:650px; margin:auto; border-radius:18px; overflow:hidden; border:1px solid #e5e7eb;">

            <div style="background:#111827; padding:30px; text-align:center;">
                <h1 style="color:#D4AF37; margin:0;">
                    Cooperativa Pirotécnica
                </h1>

                <p style="color:white; margin-top:8px;">
                    Catálogo Web
                </p>
            </div>

            <div style="padding:35px;">
                <h2 style="color:#111827;">
                    ¡Hola {usuario.first_name}!
                </h2>

                <p style="font-size:16px; color:#4b5563; line-height:1.7;">
                    Tu cuenta fue creada correctamente. Ahora puedes iniciar sesión utilizando tu
                    <strong>correo electrónico</strong> y comenzar a usar el sistema.
                </p>

                <div style="background:#f8fafc; border-left:5px solid #D4AF37; padding:18px; margin:25px 0;">
                    <strong>Con tu cuenta podrás:</strong>

                    <ul style="margin-top:12px;">
                        <li>Consultar el catálogo de productos.</li>
                        <li>Agregar productos a favoritos.</li>
                        <li>Solicitar cotizaciones.</li>
                        <li>Recibir tus cotizaciones por correo.</li>
                    </ul>
                </div>

                <p style="color:#6b7280;">
                    Gracias por registrarte en nuestro sistema.
                </p>
            </div>

            <div style="background:#111827; color:white; text-align:center; padding:18px;">
                © Cooperativa Pirotécnica
            </div>

        </div>
        """
    )

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    sg.send(mensaje)