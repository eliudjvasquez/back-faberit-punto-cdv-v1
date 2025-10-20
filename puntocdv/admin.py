from django.contrib import admin
from import_export.admin import ExportMixin
from puntocdv.models import Actividad, Evento, GanadorSorteo, InscripcionActividad, Persona, Premio, Producto, VentaProducto


@admin.register(Persona)
class PersonaAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('nombres', 'apellidos', 'fecha_nacimiento')
    search_fields = ('nombres', 'apellidos')
    list_filter = ('fecha_nacimiento',)


@admin.register(Evento)
class EventoAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'estado')
    search_fields = ('nombres', 'descripcion')
    list_filter = ('estado',)

@admin.register(Actividad)
class ActividadAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('evento', 'nombre', 'descripcion', 'precio', 'cupo')
    search_fields = ('evento__nombre',)


@admin.register(InscripcionActividad)
class InscripcionActividadAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('persona', 'actividad')
    search_fields = ('persona__nombres',)


@admin.register(Producto)
class ProductoAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('evento', 'nombre', 'descripcion', 'precio')
    list_filter = ('evento__nombre',)
    search_fields = ('evento__nombre',)


@admin.register(VentaProducto)
class VentaProductoAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('persona', 'producto', 'cantidad', 'total')
    search_fields = ('persona__nombres',)
    list_filter = ('persona__nombres',)


@admin.register(Premio)
class PremioAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'sorteo_activo', 'fecha_sorteo')
    search_fields = ('nombre',)
    list_filter = ('nombre',)


@admin.register(GanadorSorteo)
class GanadorSorteoAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('inscripcion', 'premio', 'fecha_ganado')
    search_fields = ('inscripcion__persona__nombres',)
    list_filter = ('inscripcion__persona__nombres',)


admin.site.site_header = "Punto CDV"
admin.site.site_title = "PuntoCDV"
