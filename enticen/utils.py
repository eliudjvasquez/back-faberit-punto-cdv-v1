from enticen.serializers import APIResponseSerializer
from rest_framework.response import Response
from rest_framework import status


def process_response_success(self, data, message='Se obtuvo con éxito los datos de la consulta'):
    response_serializer = APIResponseSerializer(data=dict(
        success=True,
        message=message,
        data=data,
    ))
    response_serializer.is_valid()
    return Response(response_serializer.data, status=status.HTTP_200_OK)


def process_response_failed(self, error_message, message='Ocurrio un error en la consulta'):
    response_serializer = APIResponseSerializer(data=dict(
        success=False,
        message=message,
        data={'error_message': error_message}
    ))
    response_serializer.is_valid()
    return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)
