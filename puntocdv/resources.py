# resources.py
from import_export import resources
from .models import InscripcionActividad

class InscripcionActividadResource(resources.ModelResource):
    class Meta:
        model = InscripcionActividad
        fields = (
            'id',
            'persona__nombres',
            'persona__apellidos',
            'persona__tipo_documento',
            'persona__nro_documento',
            'persona__fecha_nacimiento',
            'persona__telefono',
            'persona__email',
            'actividad__nombre',
            'estado_pago',
            'titular_pago',
            'correo_confirmado',
            'asistio',
            'actividad__precio',
        )
        export_order = fields

    def get_export_headers(self, selected_fields=None):
        headers = super().get_export_headers(selected_fields=selected_fields)
        mapping = {
            'id': 'ID Registro',
            'persona__nombres': 'Nombres',
            'persona__apellidos': 'Apellidos',
            'persona__tipo_documento': 'Tipo de Documento',
            'persona__nro_documento': 'Número de Documento',
            'persona__fecha_nacimiento': 'Fecha de Nacimiento',
            'persona__telefono': 'Teléfono',
            'persona__email': 'Correo Electrónico',
            'actividad__nombre': 'Actividad',
            'estado_pago': 'Estado del Pago',
            'titular_pago': 'Titular del Pago',
            'correo_confirmado': 'Correo Confirmado',
            'asistio': 'Asistió',
            'actividad__precio': 'Precio',
        }
        return [mapping.get(h, h) for h in headers]