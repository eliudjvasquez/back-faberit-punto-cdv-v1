from .models import *
from rest_framework import serializers


class APIResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.JSONField()


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = '__all__'


class ParameterDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParameterDetail
        fields = ['id', 'name', 'code', 'numeric_value', 'string_value', 'order', 'parameter', 'get_name_parameter',
                  'long_string_value', 'image', 'json_value', 'file', 'active']


class ApplicationSerializer(serializers.ModelSerializer):
    created_date = serializers.DateTimeField(read_only=True)
    updated_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'name', 'short_name', 'detail', 'logo', 'created_name', 'created_date', 'updated_name',
                  'updated_date']


class UbigeoDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UbigeoDepartment
        fields = '__all__'


class UbigeoProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UbigeoProvince
        fields = '__all__'


class UbigeoDistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = UbigeoDistrict
        fields = '__all__'