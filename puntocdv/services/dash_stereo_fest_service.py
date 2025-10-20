from django.db import models
from puntocdv.models import Actividad, InscripcionActividad, Producto, VentaProducto
from django.utils import timezone
from datetime import timedelta

def get_event_stats(evento_id):
    actividades = Actividad.objects.filter(evento_id=evento_id)
    
    total_cupo = actividades.aggregate(models.Sum('cupo'))['cupo__sum'] or 0
    total_inscritos = InscripcionActividad.objects.filter(actividad__evento_id=evento_id).count()


    inscripciones = InscripcionActividad.objects.filter(actividad__evento_id=evento_id)
    total_asistentes = inscripciones.filter(asistio=True).count()

    return {
        'cupos_totales': total_cupo,
        'registrados': total_inscritos,
        'asistentes': total_asistentes
    }

def get_series_inscripciones_por_dia(evento_id, days=7):
    today = timezone.now().date()
    series = []
    for i in range(days):
        day = today - timedelta(days=(days - i - 1))
        count = InscripcionActividad.objects.filter(
            actividad__evento_id=evento_id,
            created_date__date=day
        ).count()
        series.append(count)
    return series

def get_misiones_data(evento_id):
    actividades = Actividad.objects.filter(evento_id=evento_id)
    data = []
    for actividad in actividades:
        registrados = actividad.inscripciones.count()
        data.append({
            'name': actividad.nombre,
            'cuposRestantes': actividad.cupo,
            'registrados': registrados
        })
    return data

def get_stock_merch(evento_id):
    productos = Producto.objects.get(evento_id=evento_id)
    return {
        'series': [{'name': '2025', 'data': [45, 85, 65, 45, 65]}],
        'data': {'stock': productos.stock}
    }

def get_ventas_merch(evento_id):
    ventas = VentaProducto.objects.filter(producto__evento_id=evento_id)
    total_ventas = ventas.aggregate(models.Sum('cantidad'))['cantidad__sum'] or 0
    total_monto = ventas.aggregate(models.Sum('total'))['total__sum'] or 0
    series = [total_ventas]  # Para gráfico tipo barra o donut
    return series, total_ventas, total_monto

def get_ventas_servo(evento_id):
    inscripciones = InscripcionActividad.objects.filter(actividad__evento_id=evento_id)
    total_ventas = inscripciones.aggregate(models.Sum('actividad__precio'))['actividad__precio__sum'] or 0
    return total_ventas