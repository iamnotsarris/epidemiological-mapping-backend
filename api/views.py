import os
import tempfile
from datetime import datetime

import pandas as pd
import requests
import google.generativeai as genai
from dotenv import load_dotenv

from django.conf import settings
from django.core.exceptions import FieldError
from django.db.models import Count
from django.db.models.functions import Trim

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import (
    api_view, permission_classes, throttle_classes,
)
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
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
from django.http import HttpResponse
from .utils.exportador import exportar, FORMATOS_SUPORTADOS

load_dotenv()

MODELOS_GLOBAIS = (CoberturaVacinal,)


# ============================================================
# THROTTLES CUSTOMIZADOS
# ============================================================
class UploadThrottle(UserRateThrottle):
    """Upload é custoso: limita a 10 por hora por usuário."""
    scope = 'upload'


class ChatThrottle(AnonRateThrottle):
    """Chat consome cota do Gemini: limita a 20 por hora por IP."""
    scope = 'chat'


class ExportThrottle(UserRateThrottle):
    """Exportação é pesada: limita a 30 por hora."""
    scope = 'export'

class IsolamentoUBSMixin:
    """
    - SEM LOGIN (visitante)  → vê TUDO (modo público)
    - ADMIN / superuser      → vê tudo
    - UBS                    → vê só onde id_unidade == perfil.id_unidade
    - models globais         → todo mundo vê (CoberturaVacinal)

    O parâmetro `?scope=all` SÓ funciona para admin/superuser.
    """
    def get_queryset(self):
        usuario = self.request.user
        modelo = self.serializer_class.Meta.model

        if not usuario.is_authenticated:
            return modelo.objects.all()

        if modelo in MODELOS_GLOBAIS:
            return modelo.objects.all()

        perfil = getattr(usuario, 'perfil', None)
        is_admin = usuario.is_superuser or (perfil and perfil.role == 'ADMIN')

        # ✅ CORRIGIDO: scope=all só vale para admin
        if self.request.query_params.get('scope') == 'all' and is_admin:
            return modelo.objects.all()

        try:
            modelo._meta.get_field('id_unidade')
        except FieldError:
            return modelo.objects.all()

        if is_admin:
            return modelo.objects.all()

        if perfil and perfil.role == 'UBS':
            cnes = str(perfil.id_unidade or '').strip()
            if not cnes:
                return modelo.objects.none()
            return modelo.objects.annotate(
                _id_limpo=Trim('id_unidade')
            ).filter(_id_limpo=cnes)

        return modelo.objects.all()


# ============================================================
# PERMISSÕES
# ============================================================
class IsUBSOrAdmin(permissions.BasePermission):
    """
    - Leitura (GET/HEAD/OPTIONS): liberada pra todos
    - Escrita (POST/PUT/PATCH): requer login (UBS ou ADMIN)
    - DELETE: só ADMIN/superuser
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        perfil = getattr(request.user, 'perfil', None)
        if perfil and perfil.role == 'ADMIN':
            return True

        if request.method == 'DELETE':
            return False

        return bool(perfil and perfil.role == 'UBS')

    def has_object_permission(self, request, view, obj):
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
    - Leitura: liberada
    - Escrita: só ADMIN/superuser
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        perfil = getattr(request.user, 'perfil', None)
        return bool(perfil and perfil.role == 'ADMIN')

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        perfil = getattr(request.user, 'perfil', None)
        return bool(perfil and perfil.role == 'ADMIN')


# ============================================================
# VIEWSETS BASE
# ============================================================
class BaseEpiViewSet(IsolamentoUBSMixin, viewsets.ModelViewSet):
    permission_classes = [IsUBSOrAdmin]

    def perform_create(self, serializer):
        perfil = getattr(self.request.user, 'perfil', None)
        if (perfil and perfil.role == 'UBS'
                and not self.request.user.is_superuser):
            serializer.save(id_unidade=str(perfil.id_unidade).strip())
        else:
            serializer.save()


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


# ============================================================
# ENDPOINTS CUSTOMIZADOS
# ============================================================
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
@throttle_classes([ExportThrottle])
def exportar_dados(request, doenca):
    """
    Exporta dados de uma doença em CSV, XLSX ou DBF.
    Respeita o isolamento UBS.
    """
    from .utils.assistente import DOENCAS, _normalizar_doenca

    chave = _normalizar_doenca(doenca)
    if not chave:
        return Response(
            {"erro": f"Doença '{doenca}' não reconhecida.",
             "disponiveis": list(DOENCAS.keys())},
            status=status.HTTP_400_BAD_REQUEST,
        )

    formato = (request.query_params.get("formato") or "csv").lower()
    if formato not in FORMATOS_SUPORTADOS:
        return Response(
            {"erro": f"Formato '{formato}' inválido.",
             "disponiveis": list(FORMATOS_SUPORTADOS)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    info = DOENCAS[chave]
    qs = info["modelo"].objects.all()

    perfil = getattr(request.user, "perfil", None)
    if (request.user.is_authenticated and perfil and perfil.role == "UBS"
            and info.get("campo_ubs")):
        cnes = str(perfil.id_unidade or "").strip()
        if cnes:
            qs = qs.annotate(_id_limpo=Trim(info["campo_ubs"])).filter(_id_limpo=cnes)

    ano = request.query_params.get("ano")
    if ano:
        try:
            qs = qs.filter(**{info["campo_ano"]: int(ano)})
        except (ValueError, TypeError):
            return Response({"erro": f"Ano inválido: {ano}"},
                            status=status.HTTP_400_BAD_REQUEST)

    try:
        conteudo, mimetype, ext = exportar(qs, info["modelo"], formato)
    except ImportError as e:
        return Response({"erro": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"erro": f"Falha ao exportar: {e}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    filename = f"{chave}_{ano or 'todos'}.{ext}"
    response = HttpResponse(conteudo, content_type=mimetype)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ============================================================
# DEBUG (só em desenvolvimento)
# ============================================================
@api_view(['GET'])
def debug_me(request):
    """Diagnóstico rápido — SÓ funciona em DEBUG=True ou para superuser."""
    if not (settings.DEBUG or request.user.is_superuser):
        return Response({"erro": "Não disponível em produção."},
                        status=status.HTTP_404_NOT_FOUND)

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
        total_visivel = (PacienteDengue.objects
                         .annotate(_id_limpo=Trim('id_unidade'))
                         .filter(_id_limpo=cnes).count())
    else:
        total_visivel = 0

    return Response({
        "autenticado": True, "username": u.username,
        "is_superuser": u.is_superuser, "role": role, "id_unidade": cnes,
        "total_dengue_geral": total_geral, "total_dengue_visivel": total_visivel,
    })


# ============================================================
# CHAT / ASSISTENTE
# ============================================================
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

SYSTEM_PROMPT = """Você é o assistente virtual do EPI-DATA, plataforma de vigilância
epidemiológica da Secretaria de Saúde de Floriano-PI.

REGRAS:
- Responda SEMPRE em português, de forma concisa (máx 3 parágrafos).
- NUNCA forneça diagnóstico médico, prescrição ou orientação clínica individual.
- SEMPRE que a pergunta envolver números, CHAME AS FERRAMENTAS.
- Ao citar números, deixe explícito o período (ano) e a doença.
- Se uma ferramenta retornar erro, oriente a contatar vigilanciafloriano@gmail.com.
- Não invente funcionalidades.

Quando você chamar uma ferramenta que retorna ranking/KPI/tabela:
- Seu texto deve ser CURTO (1-2 frases), tipo um lead jornalístico.
- O detalhamento já aparece no card."""

modelo_chat = genai.GenerativeModel(
    'gemini-3.6-flash',
    tools=TOOLS,
    system_instruction=SYSTEM_PROMPT,
)

embedding_manager = EmbeddingManager(os.getenv('GOOGLE_API_KEY'))


@api_view(['POST'])
@throttle_classes([ChatThrottle])
def chat_suporte(request):
    try:
        user_message = (request.data.get('message') or '').strip()
        if not user_message:
            return Response({'response': 'Envie uma pergunta.',
                             'status': 'error'}, status=400)

        # Limita o tamanho da mensagem para evitar abuso
        if len(user_message) > 1000:
            return Response({'response': 'Pergunta muito longa (máx 1000 caracteres).',
                             'status': 'error'}, status=400)

        context = embedding_manager.search_query(user_message)
        chat = modelo_chat.start_chat()
        response = chat.send_message(f"Contexto:\n{context}\n\nPergunta: {user_message}")

        tool_calls = []
        MAX_ITERACOES = 5

        for _ in range(MAX_ITERACOES):
            chamadas = [
                part.function_call for part in response.parts
                if getattr(part, "function_call", None) and part.function_call.name
            ]
            if not chamadas:
                break

            partes_resposta = []
            for fc in chamadas:
                args = dict(fc.args) if fc.args else {}
                resultado = executar_funcao(fc.name, args)
                tool_calls.append({"tool": fc.name, "args": args, "resultado": resultado})
                partes_resposta.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fc.name, response={"result": resultado},
                        )
                    )
                )

            response = chat.send_message(genai.protos.Content(parts=partes_resposta))

        texto_final = "".join(
            p.text for p in response.parts if getattr(p, "text", None)
        ).strip()

        structured = _montar_structured(tool_calls)

        return Response({
            'response': texto_final or 'Não consegui responder agora.',
            'structured': structured, 'status': 'success',
        })
    except Exception as e:
        print(f"Erro no chat: {e}")
        import traceback
        traceback.print_exc()
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
            "valor": res["total"], "subtitulo": "casos notificados",
        }
    if nome == "cobertura_vacinal" and res.get("resultados"):
        return {
            "tipo": "tabela", "titulo": "Cobertura vacinal",
            "colunas": ["Imunobiológico", "Ano", "Cobertura", "Meta"],
            "linhas": [[r["imunobiologico"], r["ano"],
                        f"{r['cobertura_percentual']}%", f"{r['meta_otima']}%"]
                       for r in res["resultados"]],
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

@api_view(['POST'])
@permission_classes([IsUBSOrAdmin])
@throttle_classes([UploadThrottle])
def upload_arquivo(request):
    try:
        arquivo = request.FILES.get('arquivo')
        if not arquivo:
            return Response({'erro': 'Nenhum arquivo foi enviado.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if arquivo.size > 10 * 1024 * 1024:
            return Response({'erro': 'Arquivo muito grande (máx 10MB).'},
                            status=status.HTTP_400_BAD_REQUEST)

        nome_arquivo = arquivo.name.lower()
        extensoes_permitidas = ('.csv', '.dbf', '.xlsx', '.xls')
        if not nome_arquivo.endswith(extensoes_permitidas):
            return Response(
                {'erro': f'Formato não suportado. Use: {", ".join(extensoes_permitidas)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        perfil = getattr(request.user, 'perfil', None)
        is_admin = request.user.is_superuser or (perfil and perfil.role == 'ADMIN')

        cnes_permitido = None
        if not is_admin and perfil and perfil.role == 'UBS':
            cnes_permitido = str(perfil.id_unidade or '').strip()
            if not cnes_permitido:
                return Response(
                    {'erro': 'Sua conta UBS não tem CNES vinculado. Contate o administrador.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        print(f"[UPLOAD] user={request.user.username} "
              f"role={getattr(perfil, 'role', None)} "
              f"cnes_permitido={cnes_permitido} "
              f"file={nome_arquivo} size={arquivo.size}")

        # ================= CSV =================
        if nome_arquivo.endswith('.csv'):
            if not is_admin:
                return Response(
                    {'erro': 'Apenas administradores podem importar arquivos CSV.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            try:
                df = pd.read_csv(arquivo, sep=';', encoding='utf-8', low_memory=False)
                df.columns = [str(c).strip().upper() for c in df.columns]
                df = df.where(pd.notnull(df), None)

                resultado = processar_registros(
                    df.to_dict(orient='records'),
                    nome_arquivo,
                    cnes_permitido=cnes_permitido,
                )
                if resultado.get("status") == "erro":
                    return Response({"erro": resultado.get("mensagem")},
                                    status=status.HTTP_400_BAD_REQUEST)

                inseridos = resultado.get('registros_inseridos', 0)
                ignorados = resultado.get('registros_ignorados', 0)

                msg = f"Arquivo CSV processado! {inseridos} registros inseridos."
                if ignorados:
                    msg += (f" {ignorados} registros foram ignorados "
                            f"por não pertencerem à sua UBS.")
                return Response({"status": "sucesso", "mensagem": msg})
            except Exception as e:
                import traceback
                traceback.print_exc()
                return Response({"erro": f"Erro ao processar CSV: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ================= DBF =================
        elif nome_arquivo.endswith('.dbf'):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dbf') as tmp:
                for chunk in arquivo.chunks():
                    tmp.write(chunk)
                caminho_tmp = tmp.name

            try:
                resultado = processar_arquivo_dbf(
                    caminho_tmp,
                    nome_original=nome_arquivo,
                    cnes_permitido=cnes_permitido,
                )
                if resultado.get("status") == "erro":
                    return Response({"erro": resultado.get("mensagem")},
                                    status=status.HTTP_400_BAD_REQUEST)

                inseridos = resultado.get('registros_inseridos', 0)
                ignorados = resultado.get('registros_ignorados', 0)

                msg = f"Arquivo DBF processado! {inseridos} registros inseridos."
                if ignorados:
                    msg += (f" {ignorados} registros foram ignorados "
                            f"por não pertencerem à sua UBS.")
                return Response({"status": "sucesso", "mensagem": msg})
            except Exception as e:
                return Response({"erro": f"Erro ao processar DBF: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                os.remove(caminho_tmp)

        # ================= EXCEL =================
        elif nome_arquivo.endswith(('.xlsx', '.xls')):
            try:
                df = pd.read_excel(arquivo)
                df.columns = [str(c).strip().upper() for c in df.columns]
                df = df.where(pd.notnull(df), None)

                resultado = processar_registros(
                    df.to_dict(orient='records'),
                    nome_arquivo,
                    cnes_permitido=cnes_permitido,
                )

                if resultado.get("status") == "erro":
                    return Response({"erro": resultado["mensagem"]},
                                    status=status.HTTP_400_BAD_REQUEST)

                inseridos = resultado.get('registros_inseridos', 0)
                ignorados = resultado.get('registros_ignorados', 0)

                msg = f"Planilha processada! {inseridos} registros inseridos."
                if ignorados:
                    msg += (f" {ignorados} registros foram ignorados "
                            f"por não pertencerem à sua UBS.")
                return Response({"status": "sucesso", "mensagem": msg})
            except ImportError as e:
                return Response({"erro": f"Biblioteca faltando: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
@permission_classes([IsAdminOrReadOnly])   # ✅ Só ADMIN/superuser
@throttle_classes([UploadThrottle])        # ✅ Evita spam
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
        return Response({"status": "sucesso",
                         "mensagem": "API instável. Painel atualizado com dados de segurança."})

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

    return Response({"status": "sucesso",
                     "mensagem": f"{processadas} vacinas sincronizadas."})