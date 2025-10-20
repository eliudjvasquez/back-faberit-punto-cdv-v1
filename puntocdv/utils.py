from datetime import datetime, time, date

def convertir_fecha(fecha: date) -> datetime:
    if isinstance(fecha, date) and not isinstance(fecha, datetime):
        return datetime.combine(fecha, time.min)
    return fecha