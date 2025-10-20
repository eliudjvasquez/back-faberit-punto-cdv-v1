from django.urls import include, path
from rest_framework import routers

from .api import (
    PermissionGroupViewSet,
    LoginTraceViewSet,
    GroupViewSet,
    UserViewSet,
    ProfileViewSet,
    ChangePasswordApi
)

router = routers.DefaultRouter()
router.register(r'v1/permissions_group', PermissionGroupViewSet)
router.register(r'v1/logins_trace', LoginTraceViewSet)
router.register(r'v1/groups', GroupViewSet)
router.register(r'v1/users', UserViewSet)
router.register(r'v1/profiles', ProfileViewSet)


urlpatterns = [
    path('api/', include((router.urls, 'api'), namespace='api_segcen')),
    path('api/change_password', ChangePasswordApi.as_view(), name='api_change_password')
]