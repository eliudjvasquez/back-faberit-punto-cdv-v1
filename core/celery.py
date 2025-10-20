import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # 'enviar-correos-cada-2-horas': {
    #     'task': 'puntocdv.tasks.enviar_correos_fest_task',
    #     'schedule': crontab(minute='*/5'),
    # }
}