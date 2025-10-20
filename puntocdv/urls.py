from django.urls import include, path
from rest_framework import routers
from .api import *

router = routers.DefaultRouter()
router.register(r'v1/personas', PersonaViewSet)
router.register(r'v1/evento', EventoViewSet)
router.register(r'v1/actividad', ActividadViewSet)
router.register(r'v1/inscripcion-actividad', InscripcionActividadViewSet)
router.register(r'v1/producto', ProductoViewSet)
router.register(r'v1/venta-producto', VentaProductoViewSet)

urlpatterns = [
    path('api/', include((router.urls, 'api'), namespace='api_puntocdv')),
    path('api/v1/correo-manual/', EnvioCorreoMamualAPIView.as_view(), name='correo_manual'),
    path('api/v1/confirm-sale/', ConfirmSalesRecordAPIView.as_view(), name='confirm_sale'),
    path('api/v1/asistencia/', MarcarAsistenciaAPIView.as_view(), name='marcar_asistencia'),
    path('api/v1/inscripciones/filtrar/', InscripcionActividadFiltroAPIView.as_view(), name='inscripciones_filtrar'),
    path('api/v1/export-evento/', ExportInscripcionesEventoView.as_view(), name='export_evento'),
    path('api/v1/dashboard/eventos/', DashboardEventoAPIView.as_view(), name='dashboard_eventos'),
    path('api/v1/sorteo/<uuid:premio_id>/', SorteoPremioAPIView.as_view(), name='sorteo-premio'),
    path('api/v1/premios-ganador/', PremioConGanadorAPIView.as_view(), name='premios-ganador'),
    path("api/v1/verificar-envios-brevo/", VerificarEnviosBrevoAPIView.as_view(), name="verificar-envios-brevo")
]