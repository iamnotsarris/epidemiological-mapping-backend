from django.contrib.auth.models import Group, User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
    PacienteDengue, PacienteTuberculose, PacienteSifilis, PacienteChagas,
    PacienteViolenciaDomestica, PacienteHans, PacienteHepatite,
    PacienteAnimaisPec, PacienteIntoxicacao, PacienteLeish,
    PacienteAidsAdulto, CoberturaVacinal,
)


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class PacienteDengueSerializer(serializers.ModelSerializer):
    data_notificacao_display = serializers.SerializerMethodField()
    data_pri_sintoma_display = serializers.SerializerMethodField()
    data_nascimento_display  = serializers.SerializerMethodField()

    class Meta:
        model = PacienteDengue
        fields = "__all__"

    _MESES = ['jan','fev','mar','abr','mai','jun',
              'jul','ago','set','out','nov','dez']

    def _fmt(self, data, precisao):
        if not data or precisao == 'N':
            return None
        if precisao == 'Y':
            return str(data.year)
        if precisao == 'M':
            return f"{self._MESES[data.month-1]}/{data.year}"
        return data.strftime('%d/%m/%Y')

    def get_data_notificacao_display(self, obj):
        return self._fmt(obj.data_notificacao, obj.data_notificacao_precisao)
    def get_data_pri_sintoma_display(self, obj):
        return self._fmt(obj.data_pri_sintoma, obj.data_pri_sintoma_precisao)
    def get_data_nascimento_display(self, obj):
        return self._fmt(obj.data_nascimento, obj.data_nascimento_precisao)

class PacienteTuberculoseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteTuberculose
        fields = "__all__"

class PacienteSifilisSerializer(serializers.ModelSerializer):
    data_notificacao_display = serializers.SerializerMethodField()

    class Meta:
        model = PacienteSifilis
        fields = "__all__"

    _MESES = ['jan','fev','mar','abr','mai','jun',
              'jul','ago','set','out','nov','dez']

    def _fmt(self, data, precisao):
        if not data or precisao == 'N':
            return None
        if precisao == 'Y':
            return str(data.year)
        if precisao == 'M':
            return f"{self._MESES[data.month-1]}/{data.year}"
        return data.strftime('%d/%m/%Y')

    def get_data_notificacao_display(self, obj):
        return self._fmt(obj.data_notificacao, obj.data_notificacao_precisao)

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
    """
    Injeta role / id_unidade / username DENTRO do payload do JWT
    (não só na resposta do login). Assim o front consegue ler
    direto do token decodificado.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['username'] = user.username
        token['first_name'] = user.first_name

        perfil = getattr(user, 'perfil', None)
        if perfil:
            token['role'] = perfil.role
            token['id_unidade'] = perfil.id_unidade
        else:
            token['role'] = 'ADMIN' if user.is_superuser else 'UBS'
            token['id_unidade'] = None

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data['username'] = self.user.username
        data['first_name'] = self.user.first_name

        perfil = getattr(self.user, 'perfil', None)
        if perfil:
            data['role'] = perfil.role
            data['id_unidade'] = perfil.id_unidade
        else:
            data['role'] = 'ADMIN' if self.user.is_superuser else 'UBS'
            data['id_unidade'] = None

        return data


class CoberturaVacinalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoberturaVacinal
        fields = '__all__'