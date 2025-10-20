from io import BytesIO
import os
from celery import shared_task
from django.core.mail import get_connection
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives

import qrcode
from io import BytesIO
from email.mime.image import MIMEImage
import requests
import qrcode

from enticen.models import ParameterDetail
from .models import InscripcionActividad
from django.contrib.auth import get_user_model
User = get_user_model()

import logging
logger = logging.getLogger('puntocdv')

MAX_CORREOS_DIARIOS = 200

@shared_task(bind=True, max_retries=3)
def enviar_correos_fest_task(self):
    evento_uuid = '8d062de5-1296-4855-8195-ece770bdbf54'
    hoy = timezone.localdate()
    
    parametro = ParameterDetail.objects.filter(code='LIM_COR_BRE').first()
    if not parametro or parametro.active is False:
        logger.info("🚫 El envío de correos está deshabilitado.")
        return

    # Reset diario del contador
    if parametro.date_value != hoy:
        parametro.numeric_value = 0
        parametro.date_value = hoy
        parametro.save()

    restantes = MAX_CORREOS_DIARIOS - parametro.numeric_value
    if restantes <= 0:
        logger.info("⚠️ Límite diario alcanzado, no se enviarán más correos hoy.")
        return

    pendientes = InscripcionActividad.objects.filter(
        actividad__evento__id=evento_uuid, correo_confirmado=False
    )[:restantes]
    if not pendientes:
        logger.info("✅ No hay correos pendientes.")
        return

    # Obtiene proveedor dinámico (puede venir de otro parámetro)
    proveedor_param = ParameterDetail.objects.filter(code='MAIL_PROVIDER').first()
    proveedor = proveedor_param.text_value if proveedor_param else 'brevo'
    config = settings.EMAIL_CONFIGS.get(proveedor, settings.EMAIL_CONFIGS['brevo'])
    
    logger.info(f"📧 Usando proveedor de correo: {proveedor.upper()}")

    # Crear conexión con proveedor seleccionado
    connection = get_connection(
        host=config['EMAIL_HOST'],
        port=config['EMAIL_PORT'],
        username=config['EMAIL_HOST_USER'],
        password=config['EMAIL_HOST_PASSWORD'],
        use_tls=True
    )
    connection.open()

    for inscripcion in pendientes:
        persona = inscripcion.persona
        actividad = inscripcion.actividad
        attendee_email = persona.email
        attendee_name = f"{persona.nombres} {persona.apellidos}"

        try:
            # Datos del evento
            nombre_evento = 'Stereo Fest'
            fecha_evento = '31 de Octubre'
            hora_evento = '8 PM'
            direccion_evento = 'Av. César Vallejo 442, Lince - Lima'

            # Generar QR
            qr_img = qrcode.make(inscripcion.id)
            qr_bytes = BytesIO()
            qr_img.save(qr_bytes, format='PNG')
            qr_bytes.seek(0)

            # Banner del correo
            banner_bytes = None
            banner_path = os.path.join(settings.BASE_DIR, 'assets', 'banner-fest.jpg')
            if os.path.exists(banner_path):
                with open(banner_path, 'rb') as f:
                    banner_bytes = f.read()

            # Renderizar plantilla
            html_content = render_to_string('emails/confirmacion-fest.html', {
                'nombre_persona': attendee_name,
                'nombre_evento': nombre_evento,
                'fecha_evento': fecha_evento,
                'hora_evento': hora_evento,
                'direccion_evento': direccion_evento
            })
            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=f'Tu entrada para {nombre_evento}',
                body=text_content,
                from_email=f'Stereo Fest - Punto CDV <{config["DEFAULT_FROM_EMAIL"]}>',
                to=[attendee_email],
                connection=connection
            )
            email.attach_alternative(html_content, "text/html")

            # Adjuntar imágenes CID
            if banner_bytes:
                banner_mime = MIMEImage(banner_bytes)
                banner_mime.add_header('Content-ID', '<banner_cid>')
                email.attach(banner_mime)

            qr_mime = MIMEImage(qr_bytes.getvalue())
            qr_mime.add_header('Content-ID', '<qr_cid>')
            email.attach(qr_mime)

            # Enviar correo
            message_count = email.send()
            logger.info(f"📨 Correo enviado a {attendee_email} ({message_count} mensaje(s)).")

            # Validar envío si proveedor es BREVO
            enviado = True
            if proveedor == 'brevo':
                enviado = verificar_envio_brevo(attendee_email)

            if enviado:
                inscripcion.correo_confirmado = True
                inscripcion.save(update_fields=['correo_confirmado'])
                parametro.numeric_value += 1
                parametro.save()
                logger.info(f"✅ Confirmado correo a {attendee_email}")
            else:
                logger.warning(f"⚠️ Brevo no confirmó entrega para {attendee_email}, no se actualizará en BD.")

        except Exception as exc:
            logger.error(f"❌ Error enviando correo a {attendee_email}: {exc}")
            try:
                self.retry(exc=exc, countdown=300)
            except self.MaxRetriesExceededError:
                logger.error(f"🚨 Error definitivo enviando correo a {attendee_email}")

    connection.close()


@shared_task(bind=True, max_retries=3)
def verificar_envios_brevo_task(self, batch_size=100):
    logger.info("🔍 Iniciando verificación de correos enviados con Brevo...")

    # obtenemos registros en lotes
    pendientes = InscripcionActividad.objects.filter(correo_confirmado=True)[:batch_size]
    total = pendientes.count()
    if total == 0:
        logger.info("✅ No hay correos confirmados pendientes de verificar.")
        return

    logger.info(f"📦 Procesando lote de {total} correos para verificar en Brevo...")

    procesados = 0
    actualizados = 0

    for ins in pendientes:
        persona = ins.persona
        email_destino = persona.email
        procesados += 1

        if not verificar_envio_brevo(email_destino):
            ins.correo_confirmado = False
            ins.save(update_fields=["correo_confirmado"])
            actualizados += 1
            logger.warning(f"⚠️ Correo no entregado: {email_destino}, flag revertido a False.")
        else:
            logger.info(f"✅ Correo confirmado correctamente: {email_destino}")

    logger.info(f"🏁 Verificación completada. Procesados: {procesados}, revertidos: {actualizados}")



def verificar_envio_brevo(email_destino: str) -> bool:
    """Consulta la API de Brevo para validar si el correo fue efectivamente enviado."""
    api_key = settings.BREVO_API_KEY
    if not api_key:
        logger.warning("⚠️ No hay API key de Brevo configurada, no se puede verificar el envío.")
        return True  # asumimos que se envió si no hay forma de verificar

    url = "https://api.brevo.com/v3/smtp/statistics/events"
    params = {"event": "delivered", "email": email_destino, "limit": 1}
    headers = {"api-key": api_key}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("events"):
            return True
        return False
    except Exception as e:
        logger.error(f"Error verificando envío en Brevo para {email_destino}: {e}")
        return False