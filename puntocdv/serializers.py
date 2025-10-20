from datetime import date
from django.forms import ValidationError
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from enticen.models import ParameterDetail
from puntocdv.models import Actividad, Evento, GanadorSorteo, InscripcionActividad, Persona, Premio, Producto, VentaProducto
User = get_user_model()
class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = ['id', 'nombres', 'apellidos', 'tipo_documento', 'nro_documento', 
                  'fecha_nacimiento', 'genero', 'direccion', 'departamento', 'provincia', 
                  'distrito', 'telefono', 'email', 'get_fullname']
        

class EventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evento
        fields = '__all__'


class ActividadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actividad
        fields = '__all__'


class InscripcionActividadSerializer(serializers.ModelSerializer):
    persona = PersonaSerializer(read_only=True)
    actividad = ActividadSerializer(read_only=True)
    class Meta:
        model = InscripcionActividad
        fields = '__all__'


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'


class VentaProductoSerializer(serializers.ModelSerializer):
    persona = PersonaSerializer(read_only=True)
    producto = ProductoSerializer(read_only=True)
    class Meta:
        model = VentaProducto
        fields = '__all__'


class PremioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Premio
        fields = '__all__'


class GanadorSorteoSerializer(serializers.ModelSerializer):
    premio = PremioSerializer(read_only=True)
    inscripcion = InscripcionActividadSerializer(read_only=True)

    class Meta:
        model = GanadorSorteo
        fields = '__all__'


class RegistroPersonaActividadSerializer(serializers.Serializer):
    # Datos de Persona
    nombres = serializers.CharField(max_length=100)
    apellidos = serializers.CharField(max_length=100)
    tipo_documento = serializers.CharField(max_length=100)
    nro_documento = serializers.CharField(max_length=12)
    fecha_nacimiento = serializers.DateField()
    genero = serializers.ChoiceField(choices=Persona.GENEROS, required=False)
    direccion = serializers.CharField(required=False, allow_blank=True)
    departamento = serializers.CharField(required=False, allow_blank=True)
    provincia = serializers.CharField(required=False, allow_blank=True)
    distrito = serializers.CharField(required=False, allow_blank=True)
    telefono = serializers.CharField(required=False)
    email = serializers.EmailField()

    # Datos de Inscripción
    actividad_id = serializers.UUIDField()
    titular_pago = serializers.CharField(max_length=150, required=False, allow_blank=True)
    comprobante_pago = serializers.ImageField(required=False, allow_null=True)

    def validate(self, data):
        actividad_id = data['actividad_id']
        nro_documento = data['nro_documento']

        # 🔒 Lista de actividades bloqueadas (SOLD OUT)
        ACTIVIDADES_SOLD_OUT = [
            'aae27b93-2ebb-47e1-91e4-b40adfee7748',
            'a0988af6-ec1b-46f1-9318-a3abe57a2dca',
            '5a3ec161-2fc3-4db8-8821-969bbd59b326'
        ]

        if str(actividad_id) in ACTIVIDADES_SOLD_OUT:
            raise serializers.ValidationError("Esta actividad está SOLD OUT. Ya no se permiten más registros.")


        # Validar actividad existente
        try:
            actividad = Actividad.objects.get(id=actividad_id)
        except Actividad.DoesNotExist:
            raise serializers.ValidationError("La actividad no existe.")
        
        # Validar cupo
        if actividad.cupo <= 0:
            raise serializers.ValidationError("No hay cupos disponibles para esta actividad.")
        
        # Validar si persona ya existe y está inscrita en esta actividad
        if Persona.objects.filter(nro_documento=nro_documento).exists():
            persona = Persona.objects.get(nro_documento=nro_documento)
            if InscripcionActividad.objects.filter(actividad=actividad, persona=persona).exists():
                raise serializers.ValidationError("Ya estás registrado, pronto recibirás un correo de confirmación.")

        return data

    def create(self, validated_data):
        # Extraer datos
        actividad_id = validated_data.pop('actividad_id')
        titular_pago = validated_data.pop('titular_pago', None)
        comprobante = validated_data.pop('comprobante_pago', None)
        email = validated_data.get('email')
        nro_documento = validated_data.get('nro_documento')

        # Buscar o crear persona
        persona, persona_creada = Persona.objects.get_or_create(
            nro_documento=nro_documento,
            defaults=validated_data
        )

        # Crear usuario solo si la persona es nueva
        if persona_creada:
            user = User.objects.create(
                username=email,
                email=email,
                password=make_password(nro_documento)
            )
        else:
            user = User.objects.filter(email=email).first()

        # Crear la inscripción
        actividad = Actividad.objects.get(id=actividad_id)
        inscripcion = InscripcionActividad.objects.create(
            actividad=actividad,
            persona=persona,
            titular_pago=titular_pago,
            comprobante=comprobante
        )

        # Reducir el cupo
        actividad.cupo -= 1
        actividad.save()

        return {
            "usuario": user,
            "persona": persona,
            "entrada": inscripcion,
            "actividad": actividad
        }


class RegistroVentaProductoSerializer(serializers.Serializer):
    nombres = serializers.CharField(max_length=100)
    apellidos = serializers.CharField(max_length=100)
    tipo_documento = serializers.CharField(max_length=100)
    nro_documento = serializers.CharField(max_length=12)
    fecha_nacimiento = serializers.DateField()
    genero = serializers.ChoiceField(choices=Persona.GENEROS, required=False)
    direccion = serializers.CharField(required=False, allow_blank=True)
    departamento = serializers.CharField(required=False, allow_blank=True)
    provincia = serializers.CharField(required=False, allow_blank=True)
    distrito = serializers.CharField(required=False, allow_blank=True)
    telefono = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField()

    producto_id = serializers.UUIDField()
    cantidad = serializers.IntegerField(required=True)
    titular_pago = serializers.CharField(max_length=150, required=False, allow_blank=True)
    talla = serializers.CharField(max_length=4, required=True)
    comprobante_pago = serializers.ImageField(required=True)

    def validate(self, data):
        producto_id = data['producto_id']
        talla = data['talla']

        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            raise serializers.ValidationError("El producto no existe.")
        try:
            polo_stock = ParameterDetail.objects.get(code=talla)
        except Producto.DoesNotExist:
            raise serializers.ValidationError("No existe la talla elegida.")
        
        if polo_stock.numeric_value <= 0:
            raise serializers.ValidationError("No hay existencias para el producto.")
        
        return data

    def create(self, validated_data):
        producto_id = validated_data.pop('producto_id')
        titular_pago = validated_data.pop('titular_pago', None)
        comprobante = validated_data.pop('comprobante_pago', None)
        cantidad = validated_data.pop('cantidad')
        talla = validated_data.pop('talla')
        email = validated_data.get('email')
        nro_documento = validated_data.get('nro_documento')

        # Extraer solo los campos de Persona
        persona_data = {
            'nombres': validated_data.get('nombres'),
            'apellidos': validated_data.get('apellidos'),
            'tipo_documento': validated_data.get('tipo_documento'),
            'nro_documento': validated_data.get('nro_documento'),
            'fecha_nacimiento': validated_data.get('fecha_nacimiento'),
            'genero': validated_data.get('genero'),
            'telefono': validated_data.get('telefono', ''),
            'email': validated_data.get('email')
        }

        persona, persona_creada = Persona.objects.get_or_create(
            nro_documento=nro_documento,
            defaults=persona_data
        )

        # Crear usuario solo si la persona es nueva
        user, user_created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'password': make_password(nro_documento)
            }
        )

        # Crear la inscripción
        producto = Producto.objects.get(id=producto_id)
        venta = VentaProducto.objects.create(
            producto=producto,
            persona=persona,
            titular_pago=titular_pago,
            comprobante=comprobante,
            cantidad=cantidad,
            precio_final_unit=producto.precio,
            talla=talla
        )

        # Reducir stock del producto
        polo_stock = ParameterDetail.objects.get(code=talla)
        polo_stock.numeric_value -= cantidad  # Mejor restar la cantidad real
        polo_stock.save()
        
        producto.stock -= cantidad  # Mejor restar la cantidad real
        producto.save()

        return {
            "usuario": user,
            "persona": persona,
            "producto": producto,
            "venta": venta
        }