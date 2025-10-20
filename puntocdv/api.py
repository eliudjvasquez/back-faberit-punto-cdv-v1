from django.core.mail import get_connection, EmailMessage
from django.conf import settings
from rest_framework.response import Response
from core_permission.permissions.administrator_permissions import AdministratorReadEditPermissions
from core_permission.permissions.superadmin_permissions import SuperadminReadEditPermissions
from rest_framework import status, viewsets
from rest_condition import Or as rest_Or
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from enticen.utils import process_response_failed, process_response_success
from puntocdv.models import Actividad, Evento, InscripcionActividad, Persona, Producto, VentaProducto
from puntocdv.serializers import ActividadSerializer, EventoSerializer, InscripcionActividadSerializer, PersonaSerializer, ProductoSerializer, RegistroPersonaActividadSerializer, VentaProductoSerializer
from django.core.mail import send_mail
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
User = get_user_model()


class PersonaViewSet(viewsets.ModelViewSet):
    queryset = Persona.objects.filter(deleted_by=None)
    serializer_class = PersonaSerializer
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions),)


class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.filter(deleted_by=None)
    serializer_class = EventoSerializer
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions),)

class ActividadViewSet(viewsets.ModelViewSet):
    queryset = Actividad.objects.filter(deleted_by=None)
    serializer_class = ActividadSerializer
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions),)


class InscripcionActividadViewSet(viewsets.ModelViewSet):
    queryset = InscripcionActividad.objects.filter(deleted_by=None)
    serializer_class = InscripcionActividadSerializer
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions),)


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.filter(deleted_by=None)
    serializer_class = ProductoSerializer
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions),)


class VentaProductoViewSet(viewsets.ModelViewSet):
    queryset = VentaProducto.objects.filter(deleted_by=None)
    serializer_class = VentaProductoSerializer
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions),)

class RegistroPersonaEntradaAPIView(APIView):
    permission_classes = (AllowAny,) 

    def post(self, request):
        serializer = RegistroPersonaActividadSerializer(data=request.data)
        if serializer.is_valid():
            resultado = serializer.save()

            user = resultado['usuario']
            persona = resultado['persona']

            """ try:
                send_mail(
                    subject='Registro confirmado - Evento',
                    message=f"Hola {persona.get_fullname()}, tu registro al evento fue exitoso. "
                            f"Tu usuario es {user.username}.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[persona.email],
                    fail_silently=False,
                )
            except:
                return process_response_success(self, "Registro exitoso. Pero hubo un problema en enviar el correo de confirmación.") """
            
            return process_response_success(self, "Registro exitoso. Se enviará un correo de confirmación.")
        return process_response_failed(self, '', serializer.errors) 


class RegistroServolucionAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (AllowAny,) 

    def post(self, request):
        serializer = RegistroPersonaActividadSerializer(data=request.data)
        if serializer.is_valid():
            resultado = serializer.save()

            user = resultado['usuario']
            persona = resultado['persona']

            """ try:
                send_mail(
                    subject='Registro confirmado - Evento',
                    message=f"Hola {persona.get_fullname()}, tu registro al evento fue exitoso. "
                            f"Tu usuario es {user.username}.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[persona.email],
                    fail_silently=False,
                )
            except:
                return process_response_success(self, "Registro exitoso. Pero hubo un problema en enviar el correo de confirmación.") """
            
            return process_response_success(self, "Registro exitoso. Se enviará un correo de confirmación.")
        return process_response_failed(self, '', serializer.errors) 


class VentaProductoAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (AllowAny,) 

    def post(self, request):
        serializer = VentaProductoSerializer(data=request.data)
        if serializer.is_valid():
            resultado = serializer.save()

            user = resultado['usuario']
            persona = resultado['persona']

            """ try:
                send_mail(
                    subject='Registro confirmado - Compra de Merch',
                    message=f"Hola {persona.get_fullname()}, tu compra de merch fue exitoso. "
                            f"Tu usuario es {user.username}.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[persona.email],
                    fail_silently=False,
                )
            except:
                return process_response_success(self, "Registro exitoso. Pero hubo un problema en enviar el correo de confirmación.") """
            
            return process_response_success(self, "Registro exitoso. Se enviará un correo de confirmación.")
        return process_response_failed(self, '', serializer.errors) 


class ConfirmacionEnvioCorreoAPIView(APIView):
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions),)

    def post(self, request):
        nro_documento = request.data.get('nro_documento')
        actividad_id = request.data.get('actividad_id')
        if not nro_documento:
            return Response({
                'status': 400,
                'example_parameters': {
                    "nro_documento": "99999999"
                },
                'message': 'El parámetro nro_documento es obligatorio.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            persona = Persona.objects.get(nro_documento=nro_documento)
        except Persona.DoesNotExist:
            return Response({
                'status': 404,
                'message': f"No se encontró ninguna persona con nro_documento {nro_documento}."
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            user = User.objects.get(email=persona.email)
        except User.DoesNotExist:
            return Response({
                'status': 404,
                'message': f"No se encontró ningún usuario con el email {persona.email} asociado a la persona."
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            actividad = Actividad.objects.get(id=actividad_id)
        except Actividad.DoesNotExist:
            return Response({
                'status': 404,
                'message': f"No se encontró ninguna actividad con el id {actividad_id}."
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            connection = get_connection()
            connection.open()

            email_message = EmailMessage(
                subject='Registro confirmado',
                body=f"Hola {persona.nombres} {persona.apellidos}, tu registro ha sido exitoso. "
                     f"Tu usuario es {user.username}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[persona.email],
                connection=connection
            )
            email_message.send(fail_silently=False)
            connection.close()

            inscripcion = InscripcionActividad.objects.get(persona=persona, actividad=actividad)  # Ajusta según tu lógica
            inscripcion.correo_confirmado = True
            inscripcion.save()

            return process_response_success(self, "Se envió el correo de confirmación exitosamente.")

        except Exception as e:
            return process_response_failed(
                self,
                str(e),
                'Ha ocurrido un error en la confirmación y envío de correo.'
            )
