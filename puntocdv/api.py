from datetime import date
import os
from django.core.mail import get_connection
from django.conf import settings
import requests
from rest_framework.response import Response
from core.services.email_service import EmailService
from core_permission.permissions.administrator_permissions import AdministratorReadEditPermissions
from core_permission.permissions.promotor_permissions import PromotorReadEditPermissions
from core_permission.permissions.superadmin_permissions import SuperadminReadEditPermissions
from rest_framework import status, viewsets
from rest_condition import Or as rest_Or
from rest_framework.views import APIView
from enticen.models import ParameterDetail
from enticen.utils import process_response_failed, process_response_success
from puntocdv.constants import UUID_SERVOLUCION_EVENT, UUID_STEREO_FEST_EVENT
from puntocdv.models import Actividad, Evento, GanadorSorteo, InscripcionActividad, Persona, Premio, Producto, VentaProducto
from puntocdv.resources import InscripcionActividadResource
from puntocdv.serializers import ActividadSerializer, EventoSerializer, GanadorSorteoSerializer, InscripcionActividadSerializer, PersonaSerializer, PremioSerializer, ProductoSerializer, RegistroPersonaActividadSerializer, RegistroVentaProductoSerializer, VentaProductoSerializer
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from import_export.formats.base_formats import XLSX
from django.db import transaction
import qrcode
from io import BytesIO
from email.mime.image import MIMEImage

from puntocdv.services.dash_stereo_fest_service import get_event_stats, get_misiones_data, get_series_inscripciones_por_dia, get_stock_merch, get_ventas_merch, get_ventas_servo
from puntocdv.services.sorteo_service import realizar_sorteo
from puntocdv.tasks import verificar_envios_brevo_task
from puntocdv.views import verificar_envio_brevo

MAX_CORREOS_DIARIOS_SERVO = 50
MAX_CORREOS_DIARIOS_SALE = 50

User = get_user_model()
import logging
logger = logging.getLogger('puntocdv')


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
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions, PromotorReadEditPermissions),)


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

            ''' try:
                send_mail(
                    subject='Registro confirmado - Evento',
                    message=f'Hola {persona.get_fullname()}, tu registro al evento fue exitoso. '
                            f'Tu usuario es {user.username}.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[persona.email],
                    fail_silently=False,
                )
            except:
                return process_response_success(self, 'Registro exitoso. Pero hubo un problema en enviar el correo de confirmación.') '''
            
            return process_response_success(self, 'Registro exitoso. Se enviará un correo de confirmación.')
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

            ''' try:
                send_mail(
                    subject='Registro confirmado - Evento',
                    message=f'Hola {persona.get_fullname()}, tu registro al evento fue exitoso. '
                            f'Tu usuario es {user.username}.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[persona.email],
                    fail_silently=False,
                )
            except:
                return process_response_success(self, 'Registro exitoso. Pero hubo un problema en enviar el correo de confirmación.') '''
            
            return process_response_success(self, 'Registro exitoso. Se enviará un correo de confirmación.')
        return process_response_failed(self, '', serializer.errors) 


class RegistroVentaProductoAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (AllowAny,) 

    def post(self, request):
        serializer = RegistroVentaProductoSerializer(data=request.data)
        if serializer.is_valid():
            resultado = serializer.save()

            user = resultado['usuario']
            persona = resultado['persona']

            ''' try:
                send_mail(
                    subject='Registro confirmado - Compra de Merch',
                    message=f'Hola {persona.get_fullname()}, tu compra de merch fue exitoso. '
                            f'Tu usuario es {user.username}.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[persona.email],
                    fail_silently=False,
                )
            except:
                return process_response_success(self, 'Registro exitoso. Pero hubo un problema en enviar el correo de confirmación.') '''
            
            return process_response_success(self, 'Registro exitoso. Se enviará un correo de confirmación.')
        return process_response_failed(self, '', serializer.errors) 


class EnvioCorreoMamualAPIView(APIView):
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions),)

    def post(self, request):
        inscripcion_id = request.data.get('inscripcion_id')
        try:
            inscripcion = InscripcionActividad.objects.get(id=inscripcion_id)
        except Actividad.DoesNotExist:
            return Response({
                'status': 404,
                'message': f'No se encontró ninguna actividad con el id {inscripcion_id}.'
            }, status=status.HTTP_404_NOT_FOUND)

        connection = get_connection()
        connection.open()

        try:
            hoy = date.today()
            parametro = ParameterDetail.objects.filter(code='LIM_SER_BRE').first()
            if not parametro or parametro.active is False:
                return process_response_failed(self, 'El envío de correos está deshabilitado.', '') 

            if parametro.date_value != hoy:
                parametro.numeric_value = 0
                parametro.date_value = hoy
                parametro.save()

            restantes = MAX_CORREOS_DIARIOS_SERVO - parametro.numeric_value
            if restantes <= 0:
                return process_response_failed(self, 'Se alcanzó el límite diario de correos, no se enviarán más hoy.', '') 
    
            persona = inscripcion.persona
            actividad = inscripcion.actividad
            attendee_email = persona.email
            attendee_name = f'{persona.nombres} {persona.apellidos}'

            nombre_evento = 'Servolución'
            fecha_evento = '01 de Noviembre'
            hora_evento = '7 AM'
            direccion_evento = 'Confirmación por el canal de WhatsApp'
            nombre_actividad = actividad.nombre
            url_grupo_whatsapp = actividad.link_adicional

            # Generar QR
            qr_img = qrcode.make(inscripcion.id)
            qr_bytes = BytesIO()
            qr_img.save(qr_bytes, format='PNG')
            qr_bytes.seek(0)

            try:
                banner_path = os.path.join(settings.BASE_DIR, 'assets', 'banner-servo.jpg')
                with open(banner_path, 'rb') as f:
                    banner_bytes = f.read()
            except:
                banner_path = None

            try:
                icon_wapp_path = os.path.join(settings.BASE_DIR, 'assets', 'ico-wasp.png')
                with open(icon_wapp_path, 'rb') as f:
                    icon_wapp_bytes = f.read()
            except:
                icon_wapp_path = None

            # Renderizar plantilla
            html_content = render_to_string('emails/confirmacion-servo.html', {
                'nombre_persona': attendee_name,
                'nombre_evento': nombre_evento,
                'fecha_evento': fecha_evento,
                'hora_evento': hora_evento,
                'direccion_evento': direccion_evento,
                'nombre_actividad': nombre_actividad,
                'url_grupo_whatsapp':url_grupo_whatsapp
            })

            text_content = strip_tags(html_content)

            # Crear correo
            from_email = f'Servolución - Punto CDV <{settings.DEFAULT_FROM_EMAIL}>'
            email = EmailMultiAlternatives(
                subject=f'Tu entrada para {nombre_evento}',
                body=text_content,
                from_email=from_email,
                #to=['eliudjvasquez@gmail.com'],
                to=[attendee_email],
                connection=connection
            )
            email.attach_alternative(html_content, 'text/html')

            # Adjuntar imágenes CID
            if banner_bytes:
                logo_mime_banner = MIMEImage(banner_bytes)
                logo_mime_banner.add_header('Content-ID', '<banner_cid>')
                email.attach(logo_mime_banner)
            
            if icon_wapp_bytes:
                logo_mime_wsap = MIMEImage(icon_wapp_bytes)
                logo_mime_wsap.add_header('Content-ID', '<icon_wapp_cid>')
                email.attach(logo_mime_wsap)

            qr_mime = MIMEImage(qr_bytes.getvalue())
            qr_mime.add_header('Content-ID', '<qr_cid>')
            email.attach(qr_mime)

            email.send()
            inscripcion.correo_confirmado = True
            inscripcion.estado_pago = 'verificado'
            inscripcion.save()
            parametro.numeric_value += 1
            parametro.save()

        except Exception as exc:
            return process_response_failed(self, exc, 'El envío de correos está deshabilitado.') 

        connection.close()
        return process_response_success(self, 'Se envió el correo de confirmación exitosamente.')


class InscripcionActividadFiltroAPIView(APIView):
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions),)

    def post(self, request):
        actividad_id = request.data.get('actividad_id')
        evento_id = request.data.get('evento_id')  # 👈 Nuevo filtro
        estado_pago = request.data.get('estado_pago')
        correo_confirmado = request.data.get('correo_confirmado')
        asistio = request.data.get('asistio')

        queryset = InscripcionActividad.objects.all()

        # Filtro por Actividad
        if actividad_id:
            queryset = queryset.filter(actividad__id=actividad_id)

        # ✅ Filtro por Evento (relación desde Actividad)
        if evento_id:
            queryset = queryset.filter(actividad__evento__id=evento_id)

        # Filtro por Estado de pago
        if estado_pago:
            queryset = queryset.filter(estado_pago=estado_pago)

        # Filtro por correo confirmado (boolean)
        if correo_confirmado is not None:
            queryset = queryset.filter(correo_confirmado=str(correo_confirmado).lower() == 'true')

        # Filtro por asistencia (boolean)
        if asistio is not None:
            queryset = queryset.filter(asistio=str(asistio).lower() == 'true')

        # Validar resultados
        if not queryset.exists():
            return Response(
                {'message': 'No se encontraron registros con los filtros proporcionados.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Serialización
        serializer = InscripcionActividadSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class MarcarAsistenciaAPIView(APIView):
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions, PromotorReadEditPermissions),)

    def post(self, request):
        uuid_codigo = request.data['uuid']
        try:
            inscripcion = InscripcionActividad.objects.get(id=uuid_codigo)
            inscripcion.asistio = True
            inscripcion.save()
            return Response({'status': 'ok', 'message': 'Asistencia registrada'})
        except InscripcionActividad.DoesNotExist:
            return Response({'status': 'error', 'message': 'Código no válido'}, status=404)


class ExportInscripcionesEventoView(APIView):
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions),)

    def post(self, request, format=None):
        evento_uuid = request.data.get('evento_id')

        if not evento_uuid:
            return Response({
                "error": True,
                "message": "Debe enviar el parámetro 'evento_id' en el cuerpo de la solicitud."
            }, status=status.HTTP_400_BAD_REQUEST)

        actividad = Actividad.objects.filter(evento__id=evento_uuid)
        if not actividad.exists():
            return Response({
                "error": True,
                "message": "No se encontró un evento con ese UUID."
            }, status=status.HTTP_404_NOT_FOUND)

        queryset = InscripcionActividad.objects.filter(actividad__evento__id=evento_uuid)

        if not queryset.exists():
            return Response({
                "error": False,
                "message": "No hay inscripciones registradas para este evento.",
                "data": []
            }, status=status.HTTP_200_OK)

        dataset = InscripcionActividadResource().export(queryset)
        file_format = XLSX()
        exported_data = file_format.export_data(dataset)
        evento = Evento.objects.filter(id=evento_uuid).first()

        response = HttpResponse(exported_data, content_type=file_format.get_content_type())
        response['Content-Disposition'] = f'attachment; filename="{evento.nombre}.xlsx"'
        return response


class DashboardEventoAPIView(APIView):
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions, PromotorReadEditPermissions),)

    def get(self, request):
        stereo_id = UUID_STEREO_FEST_EVENT
        servo_id = UUID_SERVOLUCION_EVENT

        # Estadísticas generales
        stereo_stats = get_event_stats(stereo_id)
        servo_stats = get_event_stats(servo_id)

        # Misiones (actividades)
        misiones_servolucion = get_misiones_data(servo_id)

        # Stock y Ventas
        stock_merch = get_stock_merch(stereo_id)
        ventas_series, ventas_total, monto_total = get_ventas_merch(stereo_id)
        monto_total_servo = get_ventas_servo(servo_id)

        total_general = monto_total + monto_total_servo

        porcentaje_merch = (monto_total / total_general) * 100 if total_general > 0 else 0
        porcentaje_servo = (monto_total_servo / total_general) * 100 if total_general > 0 else 0

        response = {
            'stereoFestCuposRestantes': {
                'series': [{'name': 'Stereo Fest', 'data': [28, 40, 36, 52, 38, 60, 55]}],
                'data': {'cupos': stereo_stats['cupos_totales']}
            },
            'servolucionCuposRestantes': {
                'series': [{'name': 'Servolución', 'data': [10, 15, 8, 15, 7, 12, 8]}],
                'data': {'cupos': servo_stats['cupos_totales']}
            },
            'stereoFestRegistroAsistencia': {
                'series': [stereo_stats['asistentes']],
                'data': {
                    'registrados': stereo_stats['registrados'],
                    'asistentes': stereo_stats['asistentes']
                }
            },
            'servolucionRegistroAsistencia': {
                'series': [servo_stats['asistentes']],
                'data': {
                    'registrados': servo_stats['registrados'],
                    'asistentes': servo_stats['asistentes']
                }
            },
            'misionesServolucion': misiones_servolucion,
            'stockMerchChart': stock_merch,
            'ventasMerchChart': {
                'series': [{'data': [0, 20, 5, 30, 15, 45]}],
                'data': {'ventas': ventas_total}
            },
            'montosAcumuladosMerchServo': {
                'labels': ['Servolución', 'Merch'],
                'series': [int(porcentaje_servo), int(porcentaje_merch)],  # El segundo valor puedes reemplazarlo si tienes otro evento de merch
                'data': {
                    'merch': monto_total,
                    'servolucion': monto_total_servo
                }
            }
        }
        logger.info("La elaboración del Dashboard se realizó con éxito.")

        return Response(response)


class ConfirmSalesRecordAPIView(APIView):
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions),)

    def post(self, request):
        venta_id = request.data.get('venta_id')
        try:
            venta = VentaProducto.objects.get(id=venta_id)
        except VentaProducto.DoesNotExist:
            return Response({
                'status': 404,
                'message': f'No se encontró ninguna venta con el id {venta_id}.'
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            hoy = date.today()
            parametro = ParameterDetail.objects.filter(code='LIM_MER_ZOH').first()
            if not parametro or not parametro.active:
                return process_response_failed(self, 'El envío de correos está deshabilitado.', '') 

            if parametro.date_value != hoy:
                parametro.numeric_value = 0
                parametro.date_value = hoy
                parametro.save()

            restantes = MAX_CORREOS_DIARIOS_SALE - parametro.numeric_value
            if restantes <= 0:
                return process_response_failed(self, 'Se alcanzó el límite diario de correos, no se enviarán más hoy.', '')

            persona = venta.persona
            producto = venta.producto
            attendee_email = 'eliudjvasquez@gmail.com'
            #attendee_email = persona.email
            attendee_name = f'{persona.nombres} {persona.apellidos}'

            # 📌 Datos del evento
            contexto = {
                'nombre_persona': attendee_name,
                'nombre_evento': 'Stereo Fest',
                'fecha_evento': '31 de Octubre',
                'hora_evento': '8 PM',
                'direccion_evento': 'Av. César Valléjo 442 Lince - Lima',
                'producto': producto.nombre,
                'talla': venta.talla,
                'cantidad': venta.cantidad
            }

            # 🎟 Generar QR
            qr_img = qrcode.make(venta.id)
            qr_bytes = BytesIO()
            qr_img.save(qr_bytes, format='PNG')
            qr_bytes.seek(0)

            # 🖼 Leer imágenes
            images = {}
            banner_path = os.path.join(settings.BASE_DIR, 'assets', 'banner-merch.jpg')
            if os.path.exists(banner_path):
                with open(banner_path, 'rb') as f:
                    images['banner_cid'] = f.read()
            images['qr_cid'] = qr_bytes

            # ✉️ Enviar correo usando ZOHO
            try:
                enviado = EmailService.enviar_email(
                    provider='zoho',
                    header='Stereo Fest - Punto CDV',
                    subject=f'Tu merch para {contexto["nombre_evento"]}',
                    template_name='emails/confirmacion-merch.html',
                    context=contexto,
                    recipients=[attendee_email],
                    images=images
                )

                if enviado:
                    venta.correo_confirmado = True
                    venta.estado = 'pagado'
                    venta.save()
                    parametro.numeric_value += 1
                    parametro.save()
                else:
                    return process_response_failed(self, 'El correo no pudo ser enviado, no se guardaron los cambios.', '')

            except Exception as exc:
                return process_response_failed(self, f'Error al enviar el correo: {exc}', '')
        except Exception as exc:
            return process_response_failed(self, str(exc), 'Ocurrió un error al preparar el correo.') 

        return process_response_success(self, 'Se envió el correo de confirmación exitosamente.')


class SorteoPremioAPIView(APIView):
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions),)

    def post(self, request, premio_id):
        try:
            ganador = realizar_sorteo(premio_id)
            data = {
                "status": "success",
                "mensaje": f"Ganador seleccionado correctamente para '{ganador.actividad.nombre}'",
                "ganador": {
                    "persona": str(ganador.persona),
                    "email": ganador.persona.email,
                    "actividad": ganador.actividad.nombre,
                }
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, premio_id):
        ganadores = GanadorSorteo.objects.filter(premio_id=premio_id)
        serializer = GanadorSorteoSerializer(ganadores, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PremioConGanadorAPIView(APIView):
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions),)

    def get(self, request):
        premios = Premio.objects.all().order_by('nombre')
        data = []

        for premio in premios:
            ganador = (
                GanadorSorteo.objects
                .filter(premio=premio)
                .select_related('inscripcion__persona')
                .first()
            )

            data.append({
                "premio": PremioSerializer(premio).data,
                "ganador": GanadorSorteoSerializer(ganador).data if ganador else None
            })

        return Response(data, status=status.HTTP_200_OK)


class VerificarEnviosBrevoAPIView(APIView):
    permission_classes = (rest_Or(SuperadminReadEditPermissions, AdministratorReadEditPermissions),)

    def post(self, request):
        verificar_envios_brevo_task.delay()
        return Response({"detail": "✅ Tarea de verificación en segundo plano iniciada."}, status=status.HTTP_202_ACCEPTED)