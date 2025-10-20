from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources

from enticen.models import Parameter, ParameterDetail, Application


class ParameterResource(resources.ModelResource):
    class Meta:
        model = Parameter
        fields = ('id', 'name', 'code')


class ParameterDetailResource(resources.ModelResource):
    class Meta:
        model = ParameterDetail
        fields = ('id', 'parameter', 'name', 'code', 'numeric_value', 'string_value', 'long_string_value',
                  'order', 'image', 'json_value', 'file', 'active')


class ApplicationResource(resources.ModelResource):
    class Meta:
        model = Application
        fields = ('id', 'name', 'short_name', 'description', 'logo')


class ParameterAdmin(ImportExportModelAdmin):
    resource_class = ParameterResource
    list_display = ('id', 'name', 'code')


class ParameterDetailAdmin(ImportExportModelAdmin):
    resource_class = ParameterDetailResource
    list_display = ('id', 'parameter', 'name', 'code', 'numeric_value', 'string_value', 'long_string_value',
                    'order', 'image', 'json_value', 'file', 'active')


class ApplicationAdmin(ImportExportModelAdmin):
    resource_class = ApplicationResource
    list_display = ('id', 'name', 'short_name', 'description', 'logo')


admin.site.register(Parameter, ParameterAdmin)
admin.site.register(ParameterDetail, ParameterDetailAdmin)
admin.site.register(Application, ApplicationAdmin)

admin.site.site_header = "Entidad Central"
admin.site.site_title = "Enticen"
