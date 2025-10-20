from django.db import models
from initial.models import CreatedUpdatedDeleted

class Parameter(models.Model):
    name = models.CharField(max_length=150, verbose_name="Name")
    code = models.CharField(max_length=20, verbose_name="Code", unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Parameter"
        verbose_name_plural = "Parameters"


class ParameterDetail(models.Model):
    parameter = models.ForeignKey(Parameter, on_delete=models.PROTECT, verbose_name="Parameter")
    name = models.CharField(max_length=150, verbose_name="Name")
    code = models.CharField(max_length=50, verbose_name="Code", null=True, blank=True, unique=True)
    numeric_value = models.IntegerField(verbose_name="Numeric value", null=True, blank=True)
    string_value = models.CharField(max_length=150, verbose_name="String value", null=True, blank=True)
    long_string_value = models.TextField(verbose_name="Long string value", null=True, blank=True)
    order = models.IntegerField(verbose_name="Order", null=True, blank=True)
    image = models.ImageField(upload_to='image/parameter', verbose_name="Image", null=True, blank=True)
    json_value = models.JSONField(verbose_name="JSON value", null=True, blank=True)
    file = models.FileField(upload_to='file/parameter', verbose_name="File", null=True, blank=True)
    active = models.BooleanField(default=False)
    date_value = models.DateField(auto_now=True)

    def __str__(self):
        return self.name

    def get_name_parameter(self):
        if self.parameter:
            return self.parameter.name
        return None

    class Meta:
        verbose_name = "Parameter Detail"
        verbose_name_plural = "Parameters Detail"
        ordering = ["id"]


class Application(CreatedUpdatedDeleted):
    name = models.CharField(verbose_name="Name", max_length=50)
    short_name = models.CharField(verbose_name="Short Name", max_length=10)
    description = models.CharField(verbose_name="Description", max_length=250, null=True, blank=True)
    logo = models.ImageField(upload_to='image/logo', null=True, blank=True)

    def __str__(self):
        return f"{self.name} {self.short_name}"

    class Meta:
        verbose_name = "Application"
        verbose_name_plural = "Applications"
        ordering = ['-id']


class UbigeoDepartment(models.Model):
    department = models.CharField(verbose_name="Department", max_length=100)

    def __str__(self):
        return f"{self.department}"

    class Meta:
        verbose_name = "Ubigeo Department"
        verbose_name_plural = "Ubigeo Departments"
        ordering = ['id']


class UbigeoProvince(models.Model):
    province = models.CharField(verbose_name="Province", max_length=100)
    department = models.ForeignKey(UbigeoDepartment, on_delete=models.PROTECT, verbose_name="Department")

    def __str__(self):
        return f"{self.province}"

    class Meta:
        verbose_name = "Ubigeo Province"
        verbose_name_plural = "Ubigeo Provinces"
        ordering = ['id']


class UbigeoDistrict(models.Model):
    district = models.CharField(verbose_name="Name", max_length=100)
    province = models.ForeignKey(UbigeoProvince, on_delete=models.PROTECT, verbose_name="Province")

    def __str__(self):
        return f"{self.district}"

    class Meta:
        verbose_name = "Ubigeo District"
        verbose_name_plural = "Ubigeo Districts"
        ordering = ['id']