# services/sorteo_service.py
from email.mime.image import MIMEImage
from io import BytesIO
import logging
import os
from django.core.mail import send_mail
from django.db import transaction
from django.db.models.functions import Random
from django.utils import timezone
from django.conf import settings
import qrcode
from core.services.email_service import EmailService
from puntocdv.models import InscripcionActividad, Premio, GanadorSorteo, BlackListSorteo

logger = logging.getLogger(__name__)

@transaction.atomic
def realizar_sorteo(premio_id):
    premio = Premio.objects.select_for_update().get(id=premio_id)

    if premio.fecha_sorteo:
        raise Exception(
            f"⚠️ El premio '{premio.nombre}' ya fue sorteado el {premio.fecha_sorteo:%d/%m/%Y %H:%M}."
        )

    # Personas excluidas
    blacklist_ids = list(BlackListSorteo.objects.values_list("persona_id", flat=True))

    # Selección aleatoria directamente en DB
    ganador = InscripcionActividad.objects.filter(
        asistio=True,
    ).exclude(
        persona_id__in=blacklist_ids
    ).order_by(Random()).first()

    # Enviar correo con EmailService
    try:
        enviar_correo_ganador(ganador, premio)
        # Marcar el premio como sorteado
        # Registrar ganador
        GanadorSorteo.objects.create(inscripcion=ganador, premio=premio)

        # Agregar a la blacklist
        BlackListSorteo.objects.create(
            persona=ganador.persona,
            motivo=f"Ganador del premio '{premio.nombre}'",
        )
        premio.fecha_sorteo = timezone.now()
        premio.sorteo_activo = False
        premio.save()
        logger.info(f"Correo enviado a {ganador.persona.email} (ganador del premio {premio.nombre})")
    except Exception as e:
        logger.error(f"Error al enviar correo al ganador: {e}")

    logger.info(f"Sorteo completado. Ganador: {ganador.persona} - Premio: {premio.nombre}")
    return ganador


def enviar_correo_ganador(inscripcion, premio):
    """
    Envía correo de notificación al ganador del sorteo usando EmailService.
    """
    persona = inscripcion.persona

    subject = f"🎉 ¡Felicidades! Ganaste el premio '{premio.nombre}' en Stereo Fest"
    template_name = "emails/ganador_sorteo.html"  # Ajusta al nombre de tu plantilla
    context = {
        "nombres": persona.get_fullname,
        "premio": premio.nombre,
        "fecha": timezone.now().strftime("%d/%m/%Y"),
    }

    header = "Stereo Fest"
    provider = "zoho"  # o el que uses en EMAIL_CONFIGS

    # Opcional: imágenes CID si las usas en tu template
    images = {}
    banner_path = os.path.join(settings.BASE_DIR, 'assets', 'banner-fest.jpg')
    with open(banner_path, 'rb') as f:
        images["banner_cid"] = f.read()
    
    # Generar QR
    qr_img = qrcode.make(inscripcion.id)
    qr_bytes = BytesIO()
    qr_img.save(qr_bytes, format='PNG')
    qr_bytes.seek(0)
    images["qr_cid"] = qr_bytes

    # Enviar con tu servicio centralizado
    resultado = EmailService.enviar_email(
        provider=provider,
        header=header,
        subject=subject,
        template_name=template_name,
        context=context,
        recipients=[persona.email],
        images=images,
    )

    if resultado:
        logger.info(f"✅ Correo de ganador enviado a {persona.email}")
    else:
        logger.warning(f"⚠️ No se pudo enviar correo a {persona.email}")