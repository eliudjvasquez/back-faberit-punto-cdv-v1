from django.urls import include, path
from rest_framework import routers

from .api import *

router = routers.DefaultRouter()
router.register(r'v1/parameter', ParameterViewSet)
router.register(r'v1/parameter_detail', ParameterDetailViewSet)
router.register(r'v1/ubigeo_department', UbigeoDepartmentViewSet)
router.register(r'v1/ubigeo_province', UbigeoProvinceViewSet)
router.register(r'v1/ubigeo_district', UbigeoDistrictViewSet)


urlpatterns = [
    path('api/', include((router.urls, 'api'), namespace='api_enticen')),
]