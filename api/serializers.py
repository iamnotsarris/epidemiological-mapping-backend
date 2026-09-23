from django.contrib.auth.models import Group, User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import PacienteDengue, PacienteTuberculose, PacienteSifilis, PacienteChagas, PacienteViolenciaDomestica, \
    PacienteHans, PacienteHepatite, PacienteAnimaisPec, PacienteIntoxicacao, PacienteLeish, PacienteAidsAdulto, CoberturaVacinal


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class PacienteDengueSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteDengue
        fields = "__all__"

class PacienteTuberculoseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteTuberculose
        fields = "__all__"

class PacienteSifilisSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteSifilis
        fields = "__all__"

class PacienteChagasSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteChagas
        fields = "__all__"

class PacienteViolenciaDomesticaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteViolenciaDomestica
        fields = "__all__"

class PacienteHansSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteHans
        fields = "__all__"

class PacienteHepatiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteHepatite
        fields = "__all__"

class PacienteAnimaisPecSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteAnimaisPec
        fields = "__all__"

class PacienteIntoxicacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteIntoxicacao
        fields = "__all__"

class PacienteLeishSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteLeish
        fields = "__all__"

class PacienteAidsAdultoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteAidsAdulto
        fields = "__all__"

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['username'] = self.user.username
        data['first_name'] = self.user.first_name
        return data

class CoberturaVacinalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoberturaVacinal
        fields = '__all__'