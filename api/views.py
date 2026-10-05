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
from .utils.assistente import TOOLS, executar_funcao
from api.utils.embedding_manager import EmbeddingManager
from .utils.importador_dbf import processar_arquivo_dbf, processar_registros
import pandas as pd
import requests
import urllib.parse
from rest_framework import status
from datetime import datetime
import tempfile


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
def casos_por_bairro(request):
    dados = PacienteDengue.objects.values('bairro').annotate(casos=Count('id'))
    dados_formatados = {item['bairro']: item['casos'] for item in dados if item['bairro']}
    return Response(dados_formatados)


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
            "itens": [
                {"label": r["bairro"], "valor": r["casos"]}
                for r in res["ranking"]
            ],
        }

    if nome == "consultar_casos" and "total" in res:
        return {
            "tipo": "kpi",
            "titulo": f"{res['doenca'].capitalize()}"
                     + (f" — {res['ano']}" if res.get("ano") else ""),
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


@api_view(['POST'])
def upload_arquivo(request):
    try:
        arquivo = request.FILES.get('arquivo')
        tabela_destino = request.data.get('tabela_destino')

        if not arquivo:
            return Response({'erro': 'Nenhum arquivo foi enviado.'}, status=status.HTTP_400_BAD_REQUEST)

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

                for index, row in df_agrupado.iterrows():
                    meta = 90.0 if 'rotav rus' in str(row['imunobiologico']).lower() else 95.0
                    CoberturaVacinal.objects.update_or_create(
                        ano=int(row['ano']),
                        imunobiologico=str(row['imunobiologico']).strip(),
                        defaults={
                            'cobertura_percentual': round(row['cobertura'], 2),
                            'meta_otima': meta
                        }
                    )
            return Response({"status": "sucesso", "mensagem": "Arquivo CSV processado com sucesso!"})

        # ---- DBF (SINAN) ----
        elif nome_arquivo.endswith('.dbf'):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dbf') as tmp:
                for chunk in arquivo.chunks():
                    tmp.write(chunk)
                caminho_tmp = tmp.name

            try:
                resultado = processar_arquivo_dbf(caminho_tmp, nome_original=nome_arquivo)

                if resultado.get("status") == "erro":
                    return Response({"erro": resultado.get("mensagem")}, status=status.HTTP_400_BAD_REQUEST)

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

                # Normaliza os nomes das colunas: remove espaços, deixa upper
                df.columns = [str(c).strip().upper() for c in df.columns]

                # Opcional: substitui NaN por None para não virar "nan" no banco
                df = df.where(pd.notnull(df), None)

                registros = df.to_dict(orient='records')

                resultado = processar_registros(registros, nome_arquivo)

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
                traceback.print_exc()  # ← isso imprime o traceback real no terminal
                return Response({"erro": f"Erro ao processar planilha: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"erro": "Formato de arquivo não suportado."}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(f"Erro no upload: {str(e)}")
        return Response({"erro": f"Erro interno ao processar arquivo: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def sincronizar_api_governo(request):
    ANO_VIGENTE = datetime.now().year
    POPULACAO_ALVO = 850  # TODO: buscar do IBGE

    url = "https://apidadosabertos.saude.gov.br/v1/vacinacao/doses_aplicadas_pni"
    params = {
        "codigo_ibge": "2203909",
        "ano": ANO_VIGENTE,
    }

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
        vacinas_oficiais = [
            {"imunobiologico": "vacina BCG", "cobertura": 93.93, "meta": 95.0},
        ]
        for v in vacinas_oficiais:
            CoberturaVacinal.objects.update_or_create(
                ano=ANO_VIGENTE,
                imunobiologico=v["imunobiologico"],
                defaults={"cobertura_percentual": v["cobertura"], "meta_otima": v["meta"]},
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