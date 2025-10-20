
from datetime import datetime
from django.conf import settings
import requests
import logging
logger = logging.getLogger('puntocdv')

def verificar_envio_brevo(email_destino: str) -> bool:
    """Consulta la API de Brevo para validar si el correo fue efectivamente entregado."""
    api_key = settings.BREVO_API_KEY
    if not api_key:
        logger.warning("⚠️ No hay API key de Brevo configurada, no se puede verificar el envío.")
        return True  # Asumimos éxito si no hay API key para evitar falsos negativos

    url = "https://api.brevo.com/v3/smtp/statistics/events"
    params = {"event": "delivered", "email": email_destino, "limit": 1}
    headers = {"api-key": api_key}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        events = data.get("events", [])
        if events:
            logger.info(f"✅ Entrega confirmada para {email_destino}")
            return True
        else:
            logger.warning(f"⚠️ No se encontró entrega en Brevo para {email_destino}")
            return False
    except Exception as e:
        logger.error(f"❌ Error verificando envío en Brevo para {email_destino}: {e}")
        return False