from django.contrib.auth.models import Group, User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
CanalComunicacao
)

class CanalComunicacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CanalComunicacao
        fields = '__all__'