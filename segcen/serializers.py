import datetime
import uuid

from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction

from rest_framework import serializers

from puntocdv.models import Persona

from .models import Profile, PermissionsGroup, LoginTrace
from .tasks import send_email_notified_new_user
User = get_user_model()


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


class ProfileSerializer(serializers.ModelSerializer):
    created_date = serializers.DateTimeField(read_only=True)
    updated_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'user', 'address', 'birthday', 'photo', 'num_document', 'type_document', 'country',
                  'created_date', 'updated_date', 'telephone', 'names', 'father_last_name', 'mother_last_name']


class ProfileUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['address', 'birthday', 'photo', 'num_document', 'type_document', 'country', 'get_fullname',
                  'telephone', 'get_country_name', 'get_type_document_name', 'names', 'father_last_name',
                  'mother_last_name']


class UserSerializer(serializers.ModelSerializer):
    groups_names = serializers.SerializerMethodField()
    persona = serializers.SerializerMethodField() 

    def get_groups_names(self, obj):
        return obj.groups.values_list('name', flat=True)

    def get_persona(self, obj):
        persona = Persona.objects.filter(email=obj.email).first()
        if persona:
            return {
                "id": persona.id,
                "nombres": persona.nombres,
                "apellidos": persona.apellidos,
                "tipo_documento": persona.tipo_documento,
                "nro_documento": persona.nro_documento,
                "telefono": persona.telefono,
                "genero": persona.genero,
            }
        return None

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'groups', 'groups_names', 'persona', 'is_active'
        ]
        read_only_fields = ['groups_names', 'persona']

    @transaction.atomic
    def create(self, validated_data):
        groups_data = validated_data.pop('groups')
        profile_data = None

        if 'profile' in validated_data:
            profile_data = validated_data.pop('profile')

        user = super(UserSerializer, self).create(validated_data)

        password_random = str(uuid.uuid4())[:8]
        user.set_password(password_random)
        user.save()

        profile = Profile.objects.get(user=user)
        if profile_data:
            profile.names = profile_data.get('names')
            profile.father_last_name = profile_data.get('father_last_name')
            profile.mother_last_name = profile_data.get('mother_last_name')
            profile.address = profile_data.get('address')
            profile.birthday = profile_data.get('birthday')
            profile.photo = profile_data.get('photo')
            profile.type_document = profile_data.get('type_document')
            profile.num_document = profile_data.get('num_document')
            profile.country = profile_data.get('country')
            profile.telephone = profile_data.get('telephone')
            profile.save()

        for item in groups_data:
            user.groups.add(item)

        # Recopilación de data para el envío de correo al crear nuevo usuario
        user_groups = user.groups.all()
        for group in user_groups:
            group_name = group.name
        data_email = {
            'user_fullname': f"{user.first_name} {user.last_name}",
            'link_app_hs': settings.IBMSE_APP_URL,
            'user_rol': group_name,
            'username': user.username,
            'password': password_random,
            'recipient_list': user.email
        }

        send_email_notified_new_user(data_email)

        return user

    def update(self, instance, validated_data):
        groups_data = validated_data.pop('groups')
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.updated_by = validated_data.get('updated_by', instance.updated_by)
        instance.updated_date = validated_data.get('updated_date', instance.updated_date)
        instance.save()

        profile_data = None if 'profile' not in validated_data else validated_data.pop('profile')
        if profile_data:
            profile = Profile.objects.filter(user=instance)
            profile.update(
                names=profile_data.get('names'),
                father_last_name=profile_data.get('father_last_name'),
                mother_last_name=profile_data.get('mother_last_name'),
                address=profile_data.get('address'),
                birthday=profile_data.get('birthday'),
                photo=profile_data.get('photo'),
                type_document=profile_data.get('type_document'),
                num_document=profile_data.get('num_document'),
                country=profile_data.get('country'),
                telephone=profile_data.get('telephone'),
                updated_by=instance,
                updated_date=datetime.datetime.now()
            )

        instance.groups.clear()
        for item in groups_data:
            instance.groups.add(item)
        return instance


class PermissionGroupSerializer(serializers.ModelSerializer):
    created_date = serializers.DateTimeField(read_only=True)
    updated_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = PermissionsGroup
        fields = ['id', 'group', 'permission', 'application', 'get_group_name', 'get_application_name', 'created_name',
                  'created_date', 'updated_name', 'updated_date']


class LoginTraceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginTrace
        fields = ['id', 'get_username', 'get_name', 'trace']
