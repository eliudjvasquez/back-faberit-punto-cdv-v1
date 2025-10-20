import datetime
import shortuuid

from django.conf import settings
from django.contrib.auth import authenticate, logout
from django.contrib.sites.models import Site
from django.core import serializers as djserializers
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from rest_condition import Or as rest_Or
from rest_framework import viewsets, exceptions, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core_permission.permissions.administrator_permissions import AdministratorReadEditPermissions

from core_permission.permissions.superadmin_permissions import (SuperadminReadEditPermissions)
from enticen.api import AuditModelViewSet
from enticen.models import Application
from enticen.serializers import APIResponseSerializer
from initial.models import User
from .models import Group, Profile, PermissionsGroup, LoginTrace
from .serializers import GroupSerializer, UserSerializer, ProfileSerializer, \
    PermissionGroupSerializer, LoginTraceSerializer
from .tasks import send_email_notified_reset_password_user
from .views import get_initial_data_user


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.filter()
    serializer_class = GroupSerializer
    permission_classes = (rest_Or(
        SuperadminReadEditPermissions, AdministratorReadEditPermissions),)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter().order_by('-id')
    serializer_class = UserSerializer
    permission_classes = (rest_Or(
        SuperadminReadEditPermissions, AdministratorReadEditPermissions),)

    def perform_create(self, serializer):
        if self.request.user.is_anonymous:
            instance = serializer.save(updated_date=datetime.datetime.now())
        else:
            instance = serializer.save(created_by=self.request.user,
                                       updated_by=self.request.user,
                                       updated_date=datetime.datetime.now())

    def perform_update(self, serializer):
        instance = serializer.save(updated_by=self.request.user,
                                   updated_date=datetime.datetime.now())

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_date = datetime.datetime.now()
        instance.deleted_by = self.request.user
        instance.is_active = False
        instance.save()

        data = djserializers.serialize('python', [instance],
                                       fields=('id', 'username', 'email', 'first_name', 'last_name', 'groups'))[0]
        response_serializer = APIResponseSerializer(data=dict(
            success=True,
            message='Eliminado correctamente',
            data=data['fields'],
        ))
        response_serializer.is_valid()
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def staff(self):
        users = User.objects.filter(deleted_by=None, is_staff=True).order_by('first_name')
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def activate(self, request):
        try:
            user = request.data['user']
        except Exception as e:
            response_serializer = APIResponseSerializer(data=dict(
                success=False,
                message='No se han enviado los parámetros correctos para la consulta',
                data={'example_parameters': {
                    'user': 99
                }}
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=user)
            user.deleted_date = None
            user.deleted_by = None
            user.is_active = True
            user.save()

            response_serializer = APIResponseSerializer(data=dict(
                success=True,
                message='Se activó al usuario: ' + user.username,
                data=[],
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            response_serializer = APIResponseSerializer(data=dict(
                success=False,
                message='Ocurrio un error al intentar activar usuario',
                data={'error_message': str(e)}
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def deactivate(self, request):
        try:
            user = request.data['user']
        except Exception as e:
            response_serializer = APIResponseSerializer(data=dict(
                success=False,
                message='No se han enviado los parámetros correctos para la consulta',
                data={'example_parameters': {
                    'user': 99
                }}
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=user)
            user.deleted_date = datetime.datetime.now()
            user.deleted_by = self.request.user
            user.is_active = False
            user.save()

            response_serializer = APIResponseSerializer(data=dict(
                success=True,
                message='Se desactivó al usuario: ' + user.username,
                data=[],
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            response_serializer = APIResponseSerializer(data=dict(
                success=False,
                message='Ocurrió un error al intentar desactivar usuario',
                data={'error_message': str(e)}
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def reset_password(self, request):
        try:
            user = request.data['user']
        except Exception as e:
            response_serializer = APIResponseSerializer(data=dict(
                success=False,
                message='No se han enviado los parámetros correctos para la consulta',
                data={'example_parameters': {
                    'user': 99
                }}
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=user)
            password_random = shortuuid.ShortUUID().random(length=20)
            user.set_password(password_random)
            user.save()

            # Recopilación de data para el envío de correo al resetear password de usuario
            user_groups = user.groups.all()
            for group in user_groups:
                group_name = group.name
            data_email = {
                'user_fullname': f"{user.first_name} {user.last_name}",
                'link_app_ibise': settings.IBISE_APP_URL,
                'username': user.username,
                'password': password_random,
                'recipient_list': user.email
            }
            send_email_notified_reset_password_user(data_email)

            response_serializer = APIResponseSerializer(data=dict(
                success=True,
                message='Se restableció la contraseña del usuario: ' + user.username,
                data=[],
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            response_serializer = APIResponseSerializer(data=dict(
                success=False,
                message='Ocurrió un error al intentar resetear contraseña del usuario',
                data={'error_message': str(e)}
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)


class ProfileViewSet(AuditModelViewSet):
    queryset = Profile.objects.filter(deleted_by=None)
    serializer_class = ProfileSerializer
    permission_classes = (rest_Or(
        SuperadminReadEditPermissions, AdministratorReadEditPermissions),)


class PermissionGroupViewSet(AuditModelViewSet):
    queryset = PermissionsGroup.objects.filter(deleted_by=None).order_by('group')
    serializer_class = PermissionGroupSerializer
    permission_classes = (rest_Or(
        SuperadminReadEditPermissions, AdministratorReadEditPermissions),)


class CustomObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        if 'token' in request.data:
            user, token = get_initial_data_user(self, request, True)
        else:
            user, token = get_initial_data_user(self, request)

        profile = Profile.objects.get(user=user)
        group_name = []
        group_id = []

        if 'app' in request.data:
            app = int(request.data['app'])
        else:
            response_serializer = APIResponseSerializer(data=dict(
                success=False,
                message='No se han enviado el código del aplicativo',
                data={'example_parameters': {
                    'app': 99
                }}
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)

        try:
            application = Application.objects.get(pk=app, deleted_by=None)
            exist_trace = LoginTrace.objects.filter(user_id=user.pk)

            if exist_trace:
                login_trace_user = LoginTrace.objects.get(user_id=user.pk)
                trace = login_trace_user.trace
                trace.append({
                    'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'app_id': application.pk,
                    'app_name': application.name
                })
                exist_trace.update(trace=trace)
            else:
                login_trace = LoginTrace.objects.create(
                    user=user,
                    trace=[{
                        'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'app_id': application.pk,
                        'app_name': application.name
                    }]
                )
                login_trace.save()
        except Application.DoesNotExist as e:
            response_serializer = APIResponseSerializer(data=dict(
                success=False,
                message='La aplicación no existe',
                data={'error_message': str(e)}
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            raise exceptions.AuthenticationFailed(e)

        try:
            user_groups = user.groups.all()
            for group in user_groups:
                group_name.append(group.name)
                group_id.append(group.pk)
        except Exception as e:
            groups = None

        permissions_group = PermissionsGroup.objects.filter(application=app, group=group_id[0], deleted_by=None).first()

        photo = ''
        if profile.photo:
            photo = Site.objects.get_current().domain + settings.MEDIA_URL + str(profile.photo)

        login_response = {
            'status': True,
            'message': 'Bienvenido inició sesión correctamente',
            'id': user.id,
            'token': token.key,
            'username': user.username,
            'name': user.get_full_name(),
            'short_name': user.first_name,
            'email': user.email,
            'photo': photo,
            'rol_group': group_name,
            'country': profile.country.name if profile.country else '',
            'permissions': permissions_group.permission if permissions_group else '',
        }

        return Response(login_response)


class LoginTraceViewSet(viewsets.ModelViewSet):
    queryset = LoginTrace.objects.all()
    serializer_class = LoginTraceSerializer


class ChangePasswordApi(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        try:
            username = request.data['username']
            password = request.data['password']
            new_password = request.data['new_password']
            success = False

            user_in_session = authenticate(request, username=username, password=password)

            if user_in_session is not None:
                user = User.objects.get(username=username)
                user.set_password(new_password)
                user.save()

                try:
                    request.user.auth_token.delete()
                except (AttributeError, ObjectDoesNotExist):
                    pass

                logout(request)
                message = 'Se cambió el password correctamente'
                success = True

            else:
                message = 'El password ingresado no es correcto'

        except Exception as e:
            raise exceptions.AuthenticationFailed(e)

        response_serializer = APIResponseSerializer(data=dict(
            success=success,
            message=message,
            data=[],
        ))
        response_serializer.is_valid()
        return Response(response_serializer.data, status=status.HTTP_200_OK)
