from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from initial.models import CreatedUpdatedDeleted
from django.utils import timezone
import uuid


class Persona(CreatedUpdatedDeleted):
    GENEROS = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('I', 'No registrado')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    tipo_documento = models.CharField(max_length=100)
    nro_documento = models.CharField(max_length=12, unique=True, blank=True, null=True)
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=1, choices=GENEROS, blank=True)
    direccion = models.TextField(blank=True, null=True)
    departamento = models.CharField(max_length=100, blank=True)
    provincia = models.CharField(max_length=100, blank=True)
    distrito = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
    
    def get_fullname(self):
        primer_nombre = self.nombres.split()[0] if self.nombres else ''
        primer_apellido = self.apellidos.split()[0] if self.apellidos else ''
        return f"{primer_nombre} {primer_apellido}"


class Evento(CreatedUpdatedDeleted):
    ESTADO_CHOICES = [
        ('en_curso', 'En curso'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='en_curso')
    qr_pago = models.ImageField(upload_to='eventos/qr_pagos/', blank=True, null=True)
    cupo = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"

class Actividad(CreatedUpdatedDeleted):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='actividades')
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    cupo = models.PositiveIntegerField()
    link_adicional = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} - {self.evento.nombre}"


class InscripcionActividad(CreatedUpdatedDeleted):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('verificado', 'Verificado'),
        ('rechazado', 'Rechazado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='inscripciones')
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='inscripciones')
    estado_pago = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    titular_pago = models.CharField(max_length=150, null=True, blank=True)
    comprobante = models.ImageField(upload_to='comprobantes/actividades/', null=True, blank=True)
    correo_confirmado = models.BooleanField(default=False)
    asistio = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.persona} - {self.actividad.nombre}"


class Producto(CreatedUpdatedDeleted):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='productos')
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} - {self.evento.nombre}"


class VentaProducto(CreatedUpdatedDeleted):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('entregado', 'Entregado'),
    ]
    TALLAS = [
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='ventas')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='ventas')
    cantidad = models.PositiveIntegerField(default=1)
    precio_final_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    comprobante = models.ImageField(upload_to='comprobantes/ventas/', blank=True, null=True)
    titular_pago = models.CharField(max_length=150, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    talla = models.CharField(max_length=4, choices=TALLAS, default='M')
    correo_confirmado = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.total = Decimal(self.cantidad) * Decimal(self.precio_final_unit)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.persona} - {self.producto.nombre} ({self.estado})"


class Premio(CreatedUpdatedDeleted):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    sorteo_activo = models.BooleanField(default=True)
    fecha_sorteo = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class GanadorSorteo(CreatedUpdatedDeleted):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inscripcion = models.ForeignKey('InscripcionActividad', on_delete=models.CASCADE)
    premio = models.ForeignKey(Premio, on_delete=models.CASCADE)
    fecha_ganado = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('inscripcion', 'premio')  # evita duplicar ganador para el mismo premio

    def __str__(self):
        return f"{self.inscripcion.persona} - {self.premio.nombre}"


class BlackListSorteo(CreatedUpdatedDeleted):
    persona = models.ForeignKey('Persona', on_delete=models.CASCADE, unique=True)
    motivo = models.CharField(max_length=200, blank=True, null=True)
    fecha = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.persona} (excluido)"