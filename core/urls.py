"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from enticen.api import ManyParameters
from segcen.api import CustomObtainAuthToken
from puntocdv.api import RegistroPersonaEntradaAPIView, RegistroServolucionAPIView, RegistroVentaProductoAPIView

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/authorize/', CustomObtainAuthToken.as_view(), name='authorize'),
    path('api/registro-evento/', RegistroPersonaEntradaAPIView.as_view(), name='registro-evento'),
    path('api/registro-servo/', RegistroServolucionAPIView.as_view(), name='registro-servo'),
    path('api/venta-producto/', RegistroVentaProductoAPIView.as_view(), name='venta-producto'),
    path('api/many_parameters/', ManyParameters.as_view(), name='many_parameters'),
    path('segcen/', include('segcen.urls')),
    path('enticen/', include('enticen.urls')),
    path('puntocdv/', include('puntocdv.urls'))
] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)