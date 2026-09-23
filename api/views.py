from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Count, Model
from .models import PacienteDengue, PacienteHans, PacienteHepatite, PacienteAnimaisPec, PacienteIntoxicacao, PacienteLeish, PacienteAidsAdulto, CoberturaVacinal
from .serializers import PacienteDengueSerializer, PacienteTuberculoseSerializer, PacienteViolenciaDomestica, \
    PacienteSifilis, \
    PacienteSifilisSerializer, PacienteViolenciaDomesticaSerializer, PacienteChagas, PacienteChagasSerializer, PacienteHansSerializer, PacienteHepatiteSerializer, PacienteAnimaisPecSerializer, PacienteIntoxicacaoSerializer, PacienteLeishSerializer, PacienteAidsAdultoSerializer, CoberturaVacinalSerializer
from api.models import PacienteTuberculose
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
from dotenv import load_dotenv
import google.generativeai as genai
from api.utils.embedding_manager import EmbeddingManager


class PacienteDengueViewSet(viewsets.ModelViewSet):
    queryset = PacienteDengue.objects.all()
    serializer_class = PacienteDengueSerializer

class PacienteTuberculoseViewSet(viewsets.ModelViewSet):
    queryset = PacienteTuberculose.objects.all()
    serializer_class = PacienteTuberculoseSerializer

class PacienteSifilisViewSet(viewsets.ModelViewSet):
    queryset = PacienteSifilis.objects.all()
    serializer_class = PacienteSifilisSerializer

class PacienteChagasViewSet(viewsets.ModelViewSet):
    queryset = PacienteChagas.objects.all()
    serializer_class = PacienteChagasSerializer

class PacienteViolenciaDomesticaViewSet(viewsets.ModelViewSet):
    queryset = PacienteViolenciaDomestica.objects.all()
    serializer_class = PacienteViolenciaDomesticaSerializer

class PacientesHansViewSet(viewsets.ModelViewSet):
    queryset = PacienteHans.objects.all()
    serializer_class = PacienteHansSerializer

class PacientesHepatiteViewSet(viewsets.ModelViewSet):
    queryset = PacienteHepatite.objects.all()
    serializer_class = PacienteHepatiteSerializer

class PacienteAnimaisPecViewSet(viewsets.ModelViewSet):
    queryset = PacienteAnimaisPec.objects.all()
    serializer_class = PacienteAnimaisPecSerializer

class PacienteIntoxicacaoViewSet(viewsets.ModelViewSet):
    queryset = PacienteIntoxicacao.objects.all()
    serializer_class = PacienteIntoxicacaoSerializer

class PacienteLeishViewSet(viewsets.ModelViewSet):
    queryset = PacienteLeish.objects.all()
    serializer_class = PacienteLeishSerializer

class PacienteAidsAdultoViewSet(viewsets.ModelViewSet):
    queryset = PacienteAidsAdulto.objects.all()
    serializer_class = PacienteAidsAdultoSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CoberturaVacinalViewSet(viewsets.ModelViewSet):
    queryset = CoberturaVacinal.objects.all().order_by('-ano')
    serializer_class = CoberturaVacinalSerializer

@api_view(['GET'])
def casos_por_bairro(request): # funcao para agrupar o campo bairro e contar os numeros de registros
    dados = PacienteDengue.objects.values('bairro').annotate(casos=Count('id'))
    # dados formatados
    dados_formatados = {item['bairro']: item['casos'] for item in dados if item['bairro']}

    return Response(dados_formatados)


# Configuração do Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
# O modelo de geração de texto correto:
modelo_chat = genai.GenerativeModel('gemini-3.6-flash')
embedding_manager = EmbeddingManager(os.getenv('GOOGLE_API_KEY'))


@api_view(['POST'])
def chat_suporte(request):
    try:
        user_message = request.data.get('message', '')

        context = embedding_manager.search_query(user_message)

        prompt = f"""Com base apenas no seguinte contexto:

        {context}

        Responda à pergunta: {user_message}
        Responda de forma concisa e direta, em português."""

        # Gera a resposta
        response = modelo_chat.generate_content(prompt)

        return Response({
            'response': response.text,
            'status': 'success'
        })

    except Exception as e:
        print(f"Erro no chat: {str(e)}")
        return Response({
            'response': 'Desculpe, ocorreu um erro ao processar sua mensagem.',
            'status': 'error'
        }, status=500)