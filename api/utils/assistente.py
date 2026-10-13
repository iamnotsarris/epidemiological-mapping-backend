# api/utils/assistente.py
from api.models import (
    PacienteDengue, PacienteTuberculose, PacienteSifilis, PacienteChagas,
    PacienteViolenciaDomestica, PacienteHans, PacienteHepatite,
    PacienteAnimaisPec, PacienteIntoxicacao, PacienteLeish,
    PacienteAidsAdulto, CoberturaVacinal,
)

# ---- Metadados por doença ------------------------------------------------
# Campo None = o modelo não tem / não suportamos o filtro
DOENCAS = {
    "dengue": {
        "modelo": PacienteDengue,
        "campo_ano": "data_notificacao__year",
        "campo_bairro": "endereco",        # parse em memória
        "campo_ubs": "id_unidade",
        "campo_agravo": "id_agravo",
        "campo_sexo": "cs_sexo",
        "campo_classificacao": "classi_fin",
        "fonte": "SINAN Dengue",
    },
    "tuberculose": {
        "modelo": PacienteTuberculose,
        "campo_ano": "ano_notific",
        "campo_bairro": None,
        "campo_ubs": "id_unidade",
        "campo_agravo": None,
        "campo_sexo": None,
        "campo_classificacao": None,
        "fonte": "SINAN Tuberculose",
    },
    "sifilis": {
        "modelo": PacienteSifilis,
        "campo_ano": "ano_notific",
        "campo_bairro": None,
        "campo_ubs": "id_unidade",
        "campo_agravo": "id_agravo",
        "campo_sexo": None,
        "campo_classificacao": None,
        "fonte": "SINAN Sífilis",
    },
    "chagas": {
        "modelo": PacienteChagas,
        "campo_ano": "ano_notific",
        "campo_bairro": None, "campo_ubs": "id_unidade",
        "campo_agravo": None, "campo_sexo": None, "campo_classificacao": None,
        "fonte": "SINAN Chagas",
    },
    "violencia": {
        "modelo": PacienteViolenciaDomestica,
        "campo_ano": "ano_notific",
        "campo_bairro": None, "campo_ubs": "id_unidade",
        "campo_agravo": None, "campo_sexo": None, "campo_classificacao": None,
        "fonte": "SINAN Violência",
    },
    "hanseniase": {
        "modelo": PacienteHans,
        "campo_ano": "ano_notific",
        "campo_bairro": None, "campo_ubs": "id_unidade",
        "campo_agravo": None, "campo_sexo": None, "campo_classificacao": None,
        "fonte": "SINAN Hanseníase",
    },
    "hepatite": {
        "modelo": PacienteHepatite,
        "campo_ano": "ano_notific",
        "campo_bairro": None, "campo_ubs": "id_unidade",
        "campo_agravo": None, "campo_sexo": None, "campo_classificacao": None,
        "fonte": "SINAN Hepatites Virais",
    },
    "animais_peconhentos": {
        "modelo": PacienteAnimaisPec,
        "campo_ano": "ano_notific",
        "campo_bairro": None,
        "campo_ubs": "id_unidade",
        "campo_agravo": None, "campo_sexo": None, "campo_classificacao": None,
        "fonte": "SINAN Animais Peçonhentos",
    },
    "intoxicacao": {
        "modelo": PacienteIntoxicacao,
        "campo_ano": "ano_notific",
        "campo_bairro": None, "campo_ubs": "id_unidade",
        "campo_agravo": None, "campo_sexo": None, "campo_classificacao": None,
        "fonte": "SINAN Intoxicação Exógena",
    },
    "leishmaniose": {
        "modelo": PacienteLeish,
        "campo_ano": "ano_notific",
        "campo_bairro": None, "campo_ubs": "id_unidade",
        "campo_agravo": None, "campo_sexo": None, "campo_classificacao": None,
        "fonte": "SINAN Leishmaniose",
    },
    "aids": {
        "modelo": PacienteAidsAdulto,
        "campo_ano": "ano_notific",
        "campo_bairro": None, "campo_ubs": "id_unidade",
        "campo_agravo": None, "campo_sexo": None, "campo_classificacao": None,
        "fonte": "SINAN AIDS Adulto",
    },
}

ALIASES = {
    "tb": "tuberculose",
    "sífilis": "sifilis",
    "hans": "hanseniase", "hanseníase": "hanseniase",
    "violência": "violencia", "violencia domestica": "violencia",
    "violência doméstica": "violencia", "violencia domestica ": "violencia",
    "animais peconhentos": "animais_peconhentos",
    "animais peçonhentos": "animais_peconhentos",
    "intoxicação": "intoxicacao", "intoxicação exógena": "intoxicacao",
    "leish": "leishmaniose",
    "aids adulto": "aids",
    "chagas": "chagas", "doença de chagas": "chagas",
}


def _normalizar_doenca(nome: str):
    if not nome:
        return None
    key = nome.strip().lower()
    if key in DOENCAS:
        return key
    return ALIASES.get(key)


# ---- Ferramentas ---------------------------------------------------------

def consultar_casos(doenca: str, ano: int = None, bairro: str = None,
                    ubs: str = None) -> dict:
    chave = _normalizar_doenca(doenca)
    if not chave:
        return {"erro": f"Doença '{doenca}' não monitorada.",
                "disponiveis": list(DOENCAS.keys())}

    info = DOENCAS[chave]
    qs = info["modelo"].objects.all()

    if ano:
        qs = qs.filter(**{info["campo_ano"]: ano})

    avisos = []

    if bairro:
        if not info["campo_bairro"]:
            avisos.append(f"Filtro por bairro não disponível para {chave}.")
        else:
            qs = qs.filter(**{f"{info['campo_bairro']}__icontains": bairro})

    if ubs:
        if not info["campo_ubs"]:
            avisos.append(f"Filtro por UBS não disponível para {chave}.")
        else:
            qs = qs.filter(**{f"{info['campo_ubs']}__icontains": ubs})

    resultado = {
        "doenca": chave,
        "fonte": info["fonte"],
        "ano": ano,
        "total": qs.count(),
    }
    if bairro:
        resultado["bairro"] = bairro
    if ubs:
        resultado["ubs"] = ubs
    if avisos:
        resultado["aviso"] = " ".join(avisos)
    return resultado


def ranking_bairros(ano: int = None, top: int = 5) -> dict:
    """Ranking de bairros por casos de Dengue (único agravo com endereço)."""
    qs = PacienteDengue.objects.all()
    if ano:
        qs = qs.filter(data_notificacao__year=ano)

    contagem = {}
    for endereco in qs.values_list("endereco", flat=True).iterator():
        if not endereco:
            continue
        partes = [p.strip() for p in endereco.split(",") if p.strip()]
        if not partes:
            continue
        ultima = partes[-1]
        eh_cep = (ultima.isdigit() or
                  (ultima.replace("-", "").replace(".", "").isdigit()
                   and len(ultima) <= 10))
        bairro = partes[-2] if (eh_cep and len(partes) >= 2) else partes[-1]
        chave = bairro.upper()
        contagem[chave] = contagem.get(chave, 0) + 1

    ranking = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:int(top)]
    return {"doenca": "dengue", "ano": ano, "top": top,
            "ranking": [{"bairro": b, "casos": c} for b, c in ranking]}


def ranking_ubs(doenca: str, ano: int = None, top: int = 5) -> dict:
    """Ranking das UBS com mais notificações de uma doença (usa id_unidade)."""
    chave = _normalizar_doenca(doenca)
    if not chave:
        return {"erro": f"Doença '{doenca}' não monitorada."}
    info = DOENCAS[chave]
    if not info["campo_ubs"]:
        return {"erro": f"Ranking por UBS não disponível para {chave}."}

    qs = info["modelo"].objects.all()
    if ano:
        qs = qs.filter(**{info["campo_ano"]: ano})

    contagem = {}
    for valor in qs.values_list(info["campo_ubs"], flat=True).iterator():
        if not valor:
            continue
        k = str(valor).strip()
        contagem[k] = contagem.get(k, 0) + 1

    ranking = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:int(top)]
    return {"doenca": chave, "ano": ano, "top": top,
            "ranking": [{"ubs": u, "casos": c} for u, c in ranking]}


def serie_historica(doenca: str) -> dict:
    """Total de casos por ano para uma doença."""
    chave = _normalizar_doenca(doenca)
    if not chave:
        return {"erro": f"Doença '{doenca}' não monitorada."}
    info = DOENCAS[chave]

    from django.db.models import Count
    # Pra Dengue o campo é data, extrai ano via __year
    if "data_notificacao" in info["campo_ano"]:
        from django.db.models.functions import ExtractYear
        qs = (info["modelo"].objects
              .annotate(_ano=ExtractYear("data_notificacao"))
              .values("_ano")
              .annotate(total=Count("id"))
              .order_by("_ano"))
        return {"doenca": chave,
                "serie": [{"ano": r["_ano"], "casos": r["total"]} for r in qs]}

    qs = (info["modelo"].objects
          .values(info["campo_ano"])
          .annotate(total=Count("id"))
          .order_by(info["campo_ano"]))
    return {"doenca": chave,
            "serie": [{"ano": r[info["campo_ano"]], "casos": r["total"]} for r in qs]}


def distribuicao_por_agravo(doenca: str, ano: int = None) -> dict:
    """Distribuição por id_agravo (ex: sífilis adquirida/gestante/congênita)."""
    chave = _normalizar_doenca(doenca)
    if not chave:
        return {"erro": f"Doença '{doenca}' não monitorada."}
    info = DOENCAS[chave]
    if not info["campo_agravo"]:
        return {"erro": f"Distribuição por agravo não disponível para {chave}."}

    from django.db.models import Count
    qs = info["modelo"].objects.all()
    if ano:
        qs = qs.filter(**{info["campo_ano"]: ano})
    qs = (qs.values(info["campo_agravo"])
            .annotate(total=Count("id"))
            .order_by("-total"))
    return {"doenca": chave, "ano": ano,
            "distribuicao": [{"agravo": r[info["campo_agravo"]],
                              "casos": r["total"]} for r in qs]}


def cobertura_vacinal(ano: int = None, imunobiologico: str = None) -> dict:
    qs = CoberturaVacinal.objects.all()
    if ano:
        qs = qs.filter(ano=ano)
    if imunobiologico:
        qs = qs.filter(imunobiologico__icontains=imunobiologico)
    resultados = list(qs.values(
        "ano", "imunobiologico", "cobertura_percentual", "meta_otima"
    )[:30])
    return {"total": qs.count(), "resultados": resultados}


def resumo_geral(ano: int = None) -> dict:
    totais = {}
    for chave, info in DOENCAS.items():
        qs = info["modelo"].objects.all()
        if ano:
            qs = qs.filter(**{info["campo_ano"]: ano})
        totais[chave] = qs.count()
    return {"ano": ano, "totais": totais}


FUNCOES_REGISTRADAS = {
    "consultar_casos": consultar_casos,
    "ranking_bairros": ranking_bairros,
    "ranking_ubs": ranking_ubs,
    "serie_historica": serie_historica,
    "distribuicao_por_agravo": distribuicao_por_agravo,
    "cobertura_vacinal": cobertura_vacinal,
    "resumo_geral": resumo_geral,
}


def executar_funcao(nome: str, args: dict) -> dict:
    fn = FUNCOES_REGISTRADAS.get(nome)
    if not fn:
        return {"erro": f"Função '{nome}' não encontrada."}
    try:
        kwargs = {k: v for k, v in (args or {}).items() if v is not None}
        return fn(**kwargs)
    except Exception as e:
        return {"erro": f"Erro ao executar {nome}: {str(e)}"}


# ---- Declarações pra o LLM ----------------------------------------------

TOOLS = [{
    "function_declarations": [
        {
            "name": "consultar_casos",
            "description": (
                "Conta casos notificados de UMA doença, opcionalmente filtrando "
                "por ano, bairro (só dengue) e UBS. Use SEMPRE que o usuário "
                "perguntar 'quantos casos de X', 'total de X em 2024', etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "doenca": {
                        "type": "string",
                        "description": ("dengue, tuberculose, sifilis, chagas, "
                                        "violencia, hanseniase, hepatite, "
                                        "animais_peconhentos, intoxicacao, "
                                        "leishmaniose, aids")
                    },
                    "ano": {"type": "integer", "description": "Ano (opcional)"},
                    "bairro": {"type": "string",
                               "description": "Bairro — apenas dengue (opcional)"},
                    "ubs": {"type": "string",
                            "description": "CNES/nome da UBS (opcional)"}
                },
                "required": ["doenca"]
            }
        },
        {
            "name": "ranking_bairros",
            "description": "Bairros com mais casos de DENGUE, do maior pro menor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ano": {"type": "integer"},
                    "top": {"type": "integer", "description": "Padrão 5"}
                }
            }
        },
        {
            "name": "ranking_ubs",
            "description": ("UBS com mais notificações de uma doença. Use para "
                            "'qual UBS notificou mais X', 'ranking de unidades'."),
            "parameters": {
                "type": "object",
                "properties": {
                    "doenca": {"type": "string"},
                    "ano": {"type": "integer"},
                    "top": {"type": "integer"}
                },
                "required": ["doenca"]
            }
        },
        {
            "name": "serie_historica",
            "description": ("Total de casos por ano de uma doença. Use para "
                            "'evolução', 'série histórica', 'por ano'."),
            "parameters": {
                "type": "object",
                "properties": {"doenca": {"type": "string"}},
                "required": ["doenca"]
            }
        },
        {
            "name": "distribuicao_por_agravo",
            "description": ("Distribuição por tipo de agravo (ex: sífilis "
                            "adquirida/gestante/congênita). Só dengue e sífilis "
                            "têm esse campo."),
            "parameters": {
                "type": "object",
                "properties": {
                    "doenca": {"type": "string"},
                    "ano": {"type": "integer"}
                },
                "required": ["doenca"]
            }
        },
        {
            "name": "cobertura_vacinal",
            "description": "Cobertura vacinal (%) e meta por imunobiológico/ano.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ano": {"type": "integer"},
                    "imunobiologico": {"type": "string"}
                }
            }
        },
        {
            "name": "resumo_geral",
            "description": "Contagem de TODAS as doenças (panorama).",
            "parameters": {
                "type": "object",
                "properties": {"ano": {"type": "integer"}}
            }
        }
    ]
}]