from rest_framework import serializers
from .models import CanalComunicacao

class CanalComunicacaoSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)
    class Meta:
        model = CanalComunicacao
        fields = '__all__'
        read_only_fields = ('author',)