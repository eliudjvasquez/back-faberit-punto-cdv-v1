import datetime
from django.core import serializers as djserializers
from django.db.models import ProtectedError
from rest_condition import Or as rest_Or
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from core_permission.permissions.administrator_permissions import AdministratorReadEditPermissions
from core_permission.permissions.superadmin_permissions import SuperadminReadEditPermissions
from enticen.models import *
from enticen.serializers import *
from enticen.utils import process_response_success, process_response_failed


class AuditModelViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user,
                        updated_by=self.request.user,
                        updated_date=datetime.datetime.now())

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user,
                        updated_date=datetime.datetime.now())

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_date = datetime.datetime.now()
        instance.deleted_by = self.request.user
        instance.save()

        fields = [field.name for field in instance._meta.get_fields()]
        data = djserializers.serialize('python', [instance], fields=fields)[0]

        response_serializer = APIResponseSerializer(data=dict(
            success=True,
            message='Eliminado correctamente',
            data=data['fields'],
        ))
        response_serializer.is_valid()
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ParameterViewSet(viewsets.ModelViewSet):
    queryset = Parameter.objects.all().order_by('-id')
    serializer_class = ParameterSerializer
    permission_classes = (rest_Or(
        SuperadminReadEditPermissions, AdministratorReadEditPermissions),)


class ParameterDetailViewSet(viewsets.ModelViewSet):
    queryset = ParameterDetail.objects.all().order_by('-id')
    serializer_class = ParameterDetailSerializer
    permission_classes = (rest_Or(
        SuperadminReadEditPermissions, AdministratorReadEditPermissions),)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            instance.delete()

            fields = [field.name for field in instance._meta.get_fields()]
            data = djserializers.serialize('python', [instance], fields=fields)[0]

            response_serializer = APIResponseSerializer(data=dict(
                success=True,
                message='Eliminado correctamente',
                data=data['fields'],
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except ProtectedError as e:
            a, b = e.args
            msg_exception = 'No se puede eliminar el Parámetro Detalle porque se encuentra vinculado a las otras ' \
                            'entidades '
            entities = str(b)
            data = {
                'type': str(type(e)),
                'entities': entities
            }

            response_serializer = APIResponseSerializer(data=dict(
                success=False,
                message=msg_exception,
                data=data,
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def detail_list(self, request):
        try:
            parameter = request.data['parameter']
        except Exception as e:
            return Response({
                'status': 400,
                'example_parameters': {
                    "parameter": 99
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            params_det = ParameterDetail.objects.filter(parameter_id=parameter).order_by('id')
            serializer_data = self.get_serializer(params_det, many=True).data

            response_serializer = APIResponseSerializer(data=dict(
                success=True,
                message='Se obtuvo los sub parámetros',
                data=serializer_data,
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            response_serializer = APIResponseSerializer(data=dict(
                success=False,
                message='Error al obtener sub parámetros',
                data=str(e),
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)


class ApplicationViewSet(AuditModelViewSet):
    queryset = Application.objects.filter(deleted_by=None)
    serializer_class = ApplicationSerializer
    permission_classes = (rest_Or(
        SuperadminReadEditPermissions, AdministratorReadEditPermissions),)


class ManyParameters(APIView):
    permission_classes = (rest_Or(
        SuperadminReadEditPermissions, AdministratorReadEditPermissions),)
    
    def post(self, request, *args, **kwargs):
        try:
            parameter_list = request.data['parameters']
        except Exception as e:
            return Response({
                'status': 400,
                'example_parameters': {
                    "parameters": []
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = []
            if parameter_list:
                item_elements = {}
                for item in parameter_list:
                    parameters_elements = ParameterDetail.objects.filter(
                        parameter__code=item, active=True)
                    serializer = ParameterDetailSerializer(
                        parameters_elements, many=True)
                    item_elements[item] = serializer.data
                result.append(item_elements)

            response_serializer = APIResponseSerializer(data=dict(
                success=True,
                message='Se obtuvo los parámetros multiples',
                data=result,
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            response_serializer = APIResponseSerializer(data=dict(
                success=False,
                message='Error al obtener parámetros multiples',
                data=[],
            ))
            response_serializer.is_valid()
            return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)


class UbigeoDepartmentViewSet(viewsets.ModelViewSet):
    queryset = UbigeoDepartment.objects.all().order_by('id')
    serializer_class = UbigeoDepartmentSerializer
    permission_classes = (rest_Or(
        SuperadminReadEditPermissions, AdministratorReadEditPermissions),)

class UbigeoProvinceViewSet(viewsets.ModelViewSet):
    queryset = UbigeoProvince.objects.all().order_by('id')
    serializer_class = UbigeoProvinceSerializer
    permission_classes = (rest_Or(
        SuperadminReadEditPermissions, AdministratorReadEditPermissions),)

    @action(detail=False, methods=['post'])
    def by_department(self, request):
        try:
            department = request.data['department']
        except Exception as e:
            process_response_failed(self, {'parameters': {'department': 99}},
                                    'No se han enviado los parámetros correctos para la consulta')
        try:
            provinces = UbigeoProvince.objects.filter(department_id=department)
            provinces_data = UbigeoProvinceSerializer(provinces, many=True).data

            return process_response_success(self, provinces_data)
        except Exception as e:
            return process_response_failed(self, str(e))


class UbigeoDistrictViewSet(viewsets.ModelViewSet):
    queryset = UbigeoDistrict.objects.all().order_by('id')
    serializer_class = UbigeoDistrictSerializer
    permission_classes = (rest_Or(
        SuperadminReadEditPermissions, AdministratorReadEditPermissions),)

    @action(detail=False, methods=['post'])
    def by_province(self, request):
        try:
            province = request.data['province']
        except Exception as e:
            process_response_failed(self, {'parameters': {'province': 99}},
                                    'No se han enviado los parámetros correctos para la consulta')

        try:
            districts = UbigeoDistrict.objects.filter(province_id=province)
            districts_data = UbigeoDistrictSerializer(districts, many=True).data

            return process_response_success(self, districts_data)
        except Exception as e:
            return process_response_failed(self, str(e))