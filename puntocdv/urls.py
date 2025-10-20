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
    path('api/v1/send-validate', ConfirmacionEnvioCorreoAPIView.as_view(), name='validate')
]