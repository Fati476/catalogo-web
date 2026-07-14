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
                    ¡Tu cotización está lista!
                </h2>

                <p style="font-size:16px; color:#4b5563; line-height:1.7;">
                    Hemos generado correctamente la
                    <strong>cotización #{numero_cotizacion}</strong>.
                    En este correo encontrarás el archivo PDF adjunto
                    con todos los detalles de tu solicitud.
                </p>

                <div style="background:#f8fafc; border-left:5px solid #D4AF37; padding:18px; margin:25px 0;">
                    <strong>¿Qué incluye tu cotización?</strong>

                    <ul style="margin-top:12px;">
                        <li>Productos solicitados.</li>
                        <li>Precios correspondientes.</li>
                        <li>Información para dar seguimiento.</li>
                    </ul>
                </div>

                <p style="color:#6b7280;">
                    Si tienes alguna duda puedes responder a este correo
                    o comunicarte con nuestro equipo.
                </p>
            </div>

            <div style="background:#111827; color:white; text-align:center; padding:18px;">
                © Cooperativa Pirotécnica
            </div>

        </div>
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
                    Actualización de tu solicitud
                </h2>

                <p style="font-size:16px; color:#4b5563; line-height:1.7;">
                    Hemos revisado tu
                    <strong>solicitud #{numero_cotizacion}</strong>.
                    En esta ocasión no fue posible generar una cotización.
                </p>

                <div style="background:#fff8e8; border-left:5px solid #D4AF37; padding:18px; margin:25px 0;">
                    <strong>¿Qué puedes hacer?</strong>

                    <ul style="margin-top:12px;">
                        <li>Realizar una nueva solicitud.</li>
                        <li>Contactarnos para recibir orientación.</li>
                        <li>Solicitar información adicional.</li>
                    </ul>
                </div>

                <p style="color:#6b7280;">
                    Agradecemos tu comprensión y esperamos poder atenderte
                    en una próxima ocasión.
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


def enviar_bienvenida(usuario):

    mensaje = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=usuario.email,
        subject="🎉 ¡Bienvenido al Catálogo Web!",
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

                <p style="
                    font-size:16px;
                    color:#4b5563;
                    line-height:1.7;">

                    Tu cuenta ha sido creada correctamente.

                    Ahora puedes iniciar sesión utilizando tu
                    <strong>correo electrónico</strong>
                    y comenzar a utilizar el sistema.

                </p>

                <div style="
                    background:#f8fafc;
                    border-left:5px solid #D4AF37;
                    padding:18px;
                    margin:25px 0;">

                    <strong>
                        Con tu cuenta podrás:
                    </strong>

                    <ul style="margin-top:12px;">

                        <li>Consultar el catálogo de productos.</li>

                        <li>Agregar productos a favoritos.</li>

                        <li>Solicitar cotizaciones.</li>

                        <li>Recibir tus cotizaciones por correo.</li>

                    </ul>

                </div>

                <p style="color:#6b7280;">

                    Gracias por confiar en nosotros.

                    Esperamos brindarte la mejor experiencia
                    dentro del Catálogo Web.

                </p>

            </div>

            <div style="
                background:#111827;
                color:white;
                text-align:center;
                padding:18px;">

                © Cooperativa Pirotécnica

            </div>

        </div>
        """
    )

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    sg.send(mensaje)


def enviar_correo_recuperacion(usuario, reset_url):

    mensaje = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=usuario.email,
        subject="Restablecer contraseña - Catálogo Web",
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
                    Hola {usuario.first_name or usuario.email}
                </h2>

                <p style="font-size:16px; color:#4b5563; line-height:1.7;">
                    Recibimos una solicitud para restablecer la contraseña de tu cuenta.
                </p>

                <p style="font-size:16px; color:#4b5563; line-height:1.7;">
                    Haz clic en el siguiente botón para crear una nueva contraseña:
                </p>

                <div style="text-align:center; margin:30px 0;">
                    <a href="{reset_url}"
                       style="background:#C9A227; color:#111827; padding:14px 26px; border-radius:999px; text-decoration:none; font-weight:bold;">
                        Restablecer contraseña
                    </a>
                </div>

                <p style="color:#6b7280; font-size:14px;">
                    Si no solicitaste este cambio, puedes ignorar este correo.
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