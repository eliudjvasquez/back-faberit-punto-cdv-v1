from celery import shared_task
from django.core.mail import get_connection, EmailMessage
from django.conf import settings
from datetime import date
from .models import InscripcionActividad, ParameterDetail

MAX_CORREOS_DIARIOS = 5

@shared_task(bind=True, max_retries=3)
def enviar_correos_pendientes_task(self):
    hoy = date.today()
    parametro = ParameterDetail.objects.get(code='LIM_COR_BRE')

    if parametro.last_updated != hoy:
        parametro.numeric_value = 0
        parametro.date_value = hoy
        parametro.save()

    restantes = MAX_CORREOS_DIARIOS - parametro.numeric_value
    if restantes <= 0:
        print("Se alcanzó el límite diario de correos, no se enviarán más hoy.")
        return

    pendientes = InscripcionActividad.objects.filter(correo_confirmado=False)[:restantes]

    connection = get_connection()
    connection.open()

    for inscripcion in pendientes:
        try:
            persona = inscripcion.persona
            email = EmailMessage(
                subject='Registro confirmado',
                body=f"Hola {persona.username}, tu registro ha sido exitoso.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=['eliudjvasquez@gmail.com'],
                connection=connection
            )
            email.send(fail_silently=False)

            inscripcion.correo_confirmado = True
            inscripcion.save()

            parametro.numeric_value += 1
            parametro.save()
        except Exception as exc:
            try:
                self.retry(exc=exc, countdown=60)
            except self.MaxRetriesExceededError:
                print(f"Error definitivo enviando correo a {persona.email}: {exc}")

    connection.close()