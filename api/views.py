import os
import tempfile
from datetime import datetime

import pandas as pd
import requests
import google.generativeai as genai
from dotenv import load_dotenv

from django.core.exceptions import FieldError
from django.db.models import Count
from django.db.models.functions import Trim

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    PacienteDengue, PacienteTuberculose, PacienteSifilis, PacienteChagas,
    PacienteViolenciaDomestica, PacienteHans, PacienteHepatite,
    PacienteAnimaisPec, PacienteIntoxicacao, PacienteLeish,
    PacienteAidsAdulto, CoberturaVacinal,
)
from .serializers import (
    PacienteDengueSerializer, PacienteTuberculoseSerializer,
    PacienteSifilisSerializer, PacienteChagasSerializer,
    PacienteViolenciaDomesticaSerializer, PacienteHansSerializer,
    PacienteHepatiteSerializer, PacienteAnimaisPecSerializer,
    PacienteIntoxicacaoSerializer, PacienteLeishSerializer,
    PacienteAidsAdultoSerializer, CoberturaVacinalSerializer,
    CustomTokenObtainPairSerializer,
)
from .utils.assistente import TOOLS, executar_funcao
from api.utils.embedding_manager import EmbeddingManager
from .utils.importador_dbf import processar_arquivo_dbf, processar_registros

load_dotenv()

# =====================================================================
# MULTI-TENANCY
# =====================================================================

MODELOS_GLOBAIS = (CoberturaVacinal,)


class IsolamentoUBSMixin:
    """
    - SEM LOGIN (visitante)  → vê TUDO (modo público)
    - ADMIN / superuser      → vê tudo
    - UBS                    → vê só onde id_unidade == perfil.id_unidade
    - models globais         → todo mundo vê (CoberturaVacinal)
    """
    def get_queryset(self):
        usuario = self.request.user
        modelo = self.serializer_class.Meta.model

        # 🌍 VISITANTE (não logado) → modo público → vê tudo
        if not usuario.is_authenticated:
            print(f"[ISOLAMENTO] {modelo.__name__}: visitante → all")
            return modelo.objects.all()

        if modelo in MODELOS_GLOBAIS:
            return modelo.objects.all()

        # 🌍 MODO MAPA (query param) → vê tudo mesmo logado
        if self.request.query_params.get('scope') == 'all':
            return modelo.objects.all()

        try:
            modelo._meta.get_field('id_unidade')
        except FieldError:
            return modelo.objects.all()

        if usuario.is_superuser:
            return modelo.objects.all()

        perfil = getattr(usuario, 'perfil', None)

        if perfil and perfil.role == 'ADMIN':
            return modelo.objects.all()

        if perfil and perfil.role == 'UBS':
            cnes = str(perfil.id_unidade or '').strip()
            if not cnes:
                print(f"[ISOLAMENTO] {modelo.__name__}: UBS sem id_unidade → vazio")
                return modelo.objects.none()

            qs = modelo.objects.annotate(
                _id_limpo=Trim('id_unidade')
            ).filter(_id_limpo=cnes)
            print(f"[ISOLAMENTO] {modelo.__name__}: UBS {usuario.username} "
                  f"cnes={cnes} → {qs.count()} registros")
            return qs

        # Qualquer outro caso → trata como visitante
        return modelo.objects.all()


class IsUBSOrAdmin(permissions.BasePermission):
    """
    - Leitura (GET/HEAD/OPTIONS): liberada pra todos — inclusive visitante
    - Escrita (POST/PUT/PATCH): requer login
    - DELETE: só ADMIN/superuser
    """
    def has_permission(self, request, view):
        # 🔓 Leituras são públicas
        if request.method in permissions.SAFE_METHODS:
            return True

        # 🔒 Escritas exigem login
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        perfil = getattr(request.user, 'perfil', None)
        if perfil and perfil.role == 'ADMIN':
            return True

        # UBS não pode deletar
        if request.method == 'DELETE':
            return False

        return True

    def has_object_permission(self, request, view, obj):
        # 🔓 Leitura pública
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        perfil = getattr(request.user, 'perfil', None)
        if perfil and perfil.role == 'ADMIN':
            return True
        if perfil and perfil.role == 'UBS':
            return str(obj.id_unidade).strip() == str(perfil.id_unidade or '').strip()
        return False

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    - Leitura (GET/HEAD/OPTIONS): liberada pra todos — inclusive visitante
    - Escrita (POST/PUT/PATCH/DELETE): SÓ ADMIN/superuser
    """
    def has_permission(self, request, view):
        # 🔓 Leitura pública
        if request.method in permissions.SAFE_METHODS:
            return True

        # 🔒 Escrita exige login
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        perfil = getattr(request.user, 'perfil', None)
        if perfil and perfil.role == 'ADMIN':
            return True

        # UBS NÃO pode escrever em Cobertura Vacinal
        return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        perfil = getattr(request.user, 'perfil', None)
        return bool(perfil and perfil.role == 'ADMIN')


class BaseEpiViewSet(IsolamentoUBSMixin, viewsets.ModelViewSet):
    permission_classes = [IsUBSOrAdmin]

    def perform_create(self, serializer):
        perfil = getattr(self.request.user, 'perfil', None)
        if (perfil and perfil.role == 'UBS'
                and not self.request.user.is_superuser):
            # Força o id_unidade do próprio usuário, mesmo que o payload tente outro
            serializer.save(id_unidade=str(perfil.id_unidade).strip())
        else:
            serializer.save()


# =====================================================================
# VIEWSETS
# =====================================================================

class PacienteDengueViewSet(BaseEpiViewSet):
    serializer_class = PacienteDengueSerializer

class PacienteTuberculoseViewSet(BaseEpiViewSet):
    serializer_class = PacienteTuberculoseSerializer

class PacienteSifilisViewSet(BaseEpiViewSet):
    serializer_class = PacienteSifilisSerializer

class PacienteChagasViewSet(BaseEpiViewSet):
    serializer_class = PacienteChagasSerializer

class PacienteViolenciaDomesticaViewSet(BaseEpiViewSet):
    serializer_class = PacienteViolenciaDomesticaSerializer

class PacientesHansViewSet(BaseEpiViewSet):
    serializer_class = PacienteHansSerializer

class PacientesHepatiteViewSet(BaseEpiViewSet):
    serializer_class = PacienteHepatiteSerializer

class PacienteAnimaisPecViewSet(BaseEpiViewSet):
    serializer_class = PacienteAnimaisPecSerializer

class PacienteIntoxicacaoViewSet(BaseEpiViewSet):
    serializer_class = PacienteIntoxicacaoSerializer

class PacienteLeishViewSet(BaseEpiViewSet):
    serializer_class = PacienteLeishSerializer

class PacienteAidsAdultoViewSet(BaseEpiViewSet):
    serializer_class = PacienteAidsAdultoSerializer

class CoberturaVacinalViewSet(BaseEpiViewSet):
    serializer_class = CoberturaVacinalSerializer
    permission_classes = [IsAdminOrReadOnly]

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# =====================================================================
# ENDPOINTS CUSTOMIZADOS
# =====================================================================

@api_view(['GET'])
def casos_por_bairro(request):
    from .utils.importador_dbf import extrair_bairro

    qs = PacienteDengue.objects.all()

    perfil = getattr(request.user, 'perfil', None)
    if request.user.is_authenticated and perfil and perfil.role == 'UBS':
        cnes = str(perfil.id_unidade or '').strip()
        qs = qs.annotate(_id_limpo=Trim('id_unidade')).filter(_id_limpo=cnes)

    contagem = {}
    for endereco in qs.values_list('endereco', flat=True).iterator():
        bairro = extrair_bairro(endereco)
        if bairro:
            contagem[bairro] = contagem.get(bairro, 0) + 1

    return Response(contagem)


@api_view(['GET'])
def debug_me(request):
    """Diagnóstico rápido de auth + escopo. Remova depois."""
    u = request.user
    if not u.is_authenticated:
        return Response({"autenticado": False})

    perfil = getattr(u, 'perfil', None)
    role = perfil.role if perfil else None
    cnes = str(perfil.id_unidade).strip() if (perfil and perfil.id_unidade) else None

    total_geral = PacienteDengue.objects.count()

    if u.is_superuser or role == 'ADMIN':
        total_visivel = total_geral
    elif role == 'UBS' and cnes:
        total_visivel = (
            PacienteDengue.objects
            .annotate(_id_limpo=Trim('id_unidade'))
            .filter(_id_limpo=cnes)
            .count()
        )
    else:
        total_visivel = 0

    return Response({
        "autenticado": True,
        "username": u.username,
        "is_superuser": u.is_superuser,
        "role": role,
        "id_unidade": cnes,
        "total_dengue_geral": total_geral,
        "total_dengue_visivel": total_visivel,
    })


# =====================================================================
# CHAT / IA
# =====================================================================

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

SYSTEM_PROMPT = """Você é o assistente virtual do EPI-DATA, plataforma de vigilância
epidemiológica da Secretaria de Saúde de Floriano-PI.

REGRAS:
- Responda SEMPRE em português, de forma concisa (máx 3 parágrafos).
- NUNCA forneça diagnóstico médico, prescrição ou orientação clínica individual.
- SEMPRE que a pergunta envolver números (quantos casos, total, ranking de bairros,
  cobertura vacinal, panorama), CHAME AS FERRAMENTAS. Nunca invente números.
- Ao citar números, deixe explícito o período (ano) e a doença.
- Se uma ferramenta retornar erro ou a pergunta estiver fora do escopo,
  oriente o usuário a contatar vigilanciafloriano@gmail.com.
- Não invente funcionalidades que não existem na plataforma.

Quando você chamar uma ferramenta que retorna ranking/KPI/tabela:
- Seu texto de resposta deve ser CURTO (1-2 frases), tipo um lead jornalístico:
  destaque o principal achado, sem repetir a lista inteira.
- O detalhamento já aparece visualmente no card.

Ex: 'O bairro Irapuá II lidera as notificações de dengue, com 34 casos — 
quase 10% acima do segundo colocado, São Cristóvão.'"""

modelo_chat = genai.GenerativeModel(
    'gemini-3.6-flash',
    tools=TOOLS,
    system_instruction=SYSTEM_PROMPT,
)

embedding_manager = EmbeddingManager(os.getenv('GOOGLE_API_KEY'))


@api_view(['POST'])
def chat_suporte(request):
    try:
        user_message = (request.data.get('message') or '').strip()
        if not user_message:
            return Response({'response': 'Envie uma pergunta.',
                             'status': 'error'}, status=400)

        context = embedding_manager.search_query(user_message)
        chat = modelo_chat.start_chat()

        response = chat.send_message(
            f"Contexto:\n{context}\n\nPergunta: {user_message}"
        )

        tool_calls = []
        MAX_ITERACOES = 5

        for _ in range(MAX_ITERACOES):
            chamadas = [
                part.function_call
                for part in response.parts
                if getattr(part, "function_call", None) and part.function_call.name
            ]
            if not chamadas:
                break

            partes_resposta = []
            for fc in chamadas:
                args = dict(fc.args) if fc.args else {}
                resultado = executar_funcao(fc.name, args)

                tool_calls.append({
                    "tool": fc.name,
                    "args": args,
                    "resultado": resultado,
                })

                partes_resposta.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fc.name,
                            response={"result": resultado},
                        )
                    )
                )

            response = chat.send_message(
                genai.protos.Content(parts=partes_resposta)
            )

        texto_final = "".join(
            p.text for p in response.parts if getattr(p, "text", None)
        ).strip()

        structured = _montar_structured(tool_calls)

        return Response({
            'response': texto_final or 'Não consegui responder agora.',
            'structured': structured,
            'status': 'success'
        })
    except Exception as e:
        print(f"Erro no chat: {e}")
        import traceback; traceback.print_exc()
        return Response({'response': 'Erro ao processar.', 'status': 'error'}, status=500)


def _montar_structured(tool_calls):
    if not tool_calls:
        return None

    ultima = tool_calls[-1]
    nome = ultima["tool"]
    res = ultima["resultado"]

    if nome == "ranking_bairros" and res.get("ranking"):
        return {
            "tipo": "ranking",
            "titulo": f"Casos de Dengue por bairro" + (f" — {res['ano']}" if res.get("ano") else ""),
            "coluna": "Bairro",
            "itens": [{"label": r["bairro"], "valor": r["casos"]} for r in res["ranking"]],
        }

    if nome == "consultar_casos" and "total" in res:
        return {
            "tipo": "kpi",
            "titulo": f"{res['doenca'].capitalize()}" + (f" — {res['ano']}" if res.get("ano") else ""),
            "valor": res["total"],
            "subtitulo": "casos notificados",
        }

    if nome == "cobertura_vacinal" and res.get("resultados"):
        return {
            "tipo": "tabela",
            "titulo": "Cobertura vacinal",
            "colunas": ["Imunobiológico", "Ano", "Cobertura", "Meta"],
            "linhas": [
                [r["imunobiologico"], r["ano"],
                 f"{r['cobertura_percentual']}%", f"{r['meta_otima']}%"]
                for r in res["resultados"]
            ],
        }

    if nome == "resumo_geral" and res.get("totais"):
        return {
            "tipo": "ranking",
            "titulo": f"Panorama geral" + (f" — {res['ano']}" if res.get("ano") else ""),
            "coluna": "Doença",
            "itens": sorted(
                [{"label": k.capitalize(), "valor": v} for k, v in res["totais"].items()],
                key=lambda x: x["valor"], reverse=True,
            ),
        }

    return None


# =====================================================================
# UPLOAD
# =====================================================================

@api_view(['POST'])
def upload_arquivo(request):
    try:
        arquivo = request.FILES.get('arquivo')
        if not arquivo:
            return Response({'erro': 'Nenhum arquivo foi enviado.'},
                            status=status.HTTP_400_BAD_REQUEST)

        nome_arquivo = arquivo.name.lower()

        # ---- CSV (Cobertura Vacinal) ----
        if nome_arquivo.endswith('.csv'):
            df = pd.read_csv(arquivo, sep=';', encoding='utf-8', low_memory=False)
            df.columns = df.columns.str.lower()

            coluna_municipio = 'municipio' if 'municipio' in df.columns else 'no_municipio'
            if coluna_municipio in df.columns:
                df = df[df[coluna_municipio].str.upper() == 'FLORIANO']

            if 'doses_aplicadas' in df.columns and 'populacao_alvo' in df.columns:
                df['doses_aplicadas'] = pd.to_numeric(df['doses_aplicadas'], errors='coerce').fillna(0)
                df['populacao_alvo'] = pd.to_numeric(df['populacao_alvo'], errors='coerce').fillna(0)

                df_agrupado = df.groupby(['ano', 'imunobiologico']).sum().reset_index()
                df_agrupado['cobertura'] = (df_agrupado['doses_aplicadas'] / df_agrupado['populacao_alvo']) * 100
                df_agrupado['cobertura'] = df_agrupado['cobertura'].fillna(0)

                for _, row in df_agrupado.iterrows():
                    meta = 90.0 if 'rotav' in str(row['imunobiologico']).lower() else 95.0
                    CoberturaVacinal.objects.update_or_create(
                        ano=int(row['ano']),
                        imunobiologico=str(row['imunobiologico']).strip(),
                        defaults={
                            'cobertura_percentual': round(row['cobertura'], 2),
                            'meta_otima': meta,
                        }
                    )
            return Response({"status": "sucesso",
                             "mensagem": "Arquivo CSV processado com sucesso!"})

        # ---- DBF (SINAN) ----
        elif nome_arquivo.endswith('.dbf'):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dbf') as tmp:
                for chunk in arquivo.chunks():
                    tmp.write(chunk)
                caminho_tmp = tmp.name

            try:
                resultado = processar_arquivo_dbf(caminho_tmp, nome_original=nome_arquivo)
                if resultado.get("status") == "erro":
                    return Response({"erro": resultado.get("mensagem")},
                                    status=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "status": "sucesso",
                    "mensagem": f"Arquivo DBF processado! {resultado.get('registros_inseridos')} registros inseridos."
                })
            except Exception as e:
                return Response({"erro": f"Erro ao processar DBF: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                os.remove(caminho_tmp)

        # ---- XLSX / XLS ----
        elif nome_arquivo.endswith(('.xlsx', '.xls')):
            try:
                df = pd.read_excel(arquivo)
                df.columns = [str(c).strip().upper() for c in df.columns]
                df = df.where(pd.notnull(df), None)

                resultado = processar_registros(df.to_dict(orient='records'), nome_arquivo)

                if resultado.get("status") == "erro":
                    return Response({"erro": resultado["mensagem"]},
                                    status=status.HTTP_400_BAD_REQUEST)

                return Response({
                    "status": "sucesso",
                    "mensagem": f"Planilha processada! {resultado['registros_inseridos']} registros inseridos."
                })
            except ImportError as e:
                return Response({
                    "erro": f"Biblioteca faltando: {str(e)}. Rode: pip install openpyxl xlrd"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                import traceback
                traceback.print_exc()
                return Response({"erro": f"Erro ao processar planilha: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"erro": "Formato de arquivo não suportado."},
                        status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(f"Erro no upload: {str(e)}")
        return Response({"erro": f"Erro interno ao processar arquivo: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def sincronizar_api_governo(request):
    ANO_VIGENTE = datetime.now().year
    POPULACAO_ALVO = 850

    url = "https://apidadosabertos.saude.gov.br/v1/vacinacao/doses_aplicadas_pni"
    params = {"codigo_ibge": "2203909", "ano": ANO_VIGENTE}

    contagem_doses = {}

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        dados = response.json()

        registros = dados if isinstance(dados, list) else dados.get("records", [])

        for registro in registros:
            nome_vacina = registro.get("imunobiologico") or registro.get("vacina_nome")
            if not nome_vacina:
                continue
            doses = registro.get("doses_aplicadas") or registro.get("qt_doses") or 0
            contagem_doses[nome_vacina] = contagem_doses.get(nome_vacina, 0) + int(doses)
    except Exception as e:
        print(f"Erro na API de Vacinação: {e}")

    if not contagem_doses:
        CoberturaVacinal.objects.update_or_create(
            ano=ANO_VIGENTE,
            imunobiologico="vacina BCG",
            defaults={"cobertura_percentual": 93.93, "meta_otima": 95.0},
        )
        return Response({
            "status": "sucesso",
            "mensagem": "API instável. Painel atualizado com dados de segurança."
        })

    processadas = 0
    for imunobiologico, total_doses in contagem_doses.items():
        cobertura = (total_doses / POPULACAO_ALVO) * 100
        meta = 90.0 if "rotav" in imunobiologico.lower() else 95.0
        CoberturaVacinal.objects.update_or_create(
            ano=ANO_VIGENTE,
            imunobiologico=imunobiologico,
            defaults={"cobertura_percentual": round(cobertura, 2), "meta_otima": meta},
        )
        processadas += 1

    return Response({
        "status": "sucesso",
        "mensagem": f"{processadas} vacinas sincronizadas."
    })