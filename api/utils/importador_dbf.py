import os
from api.models import (
    PacienteDengue, PacienteTuberculose, PacienteSifilis, PacienteViolenciaDomestica,
    PacienteChagas, PacienteHans, PacienteHepatite, PacienteAnimaisPec,
    PacienteIntoxicacao, PacienteLeish, PacienteAidsAdulto, CoberturaVacinal,
)
from dbfread import DBF
from datetime import datetime, date
import unicodedata

MAPEA_ENDEMIAS = {
    'deng': PacienteDengue,
    'tubercu': PacienteTuberculose,
    'sifi': PacienteSifilis,
    'violencia': PacienteViolenciaDomestica,
    'chagas': PacienteChagas,
    'hans': PacienteHans,
    'hepatite': PacienteHepatite,
    'animaispec': PacienteAnimaisPec,
    'intoxicacao': PacienteIntoxicacao,
    'leish': PacienteLeish,
    'aidsadulto': PacienteAidsAdulto,
    'coberturavacinal': CoberturaVacinal,
}

BAIRRO_PARA_UBS_NOME = {
    "CENTRO": "UBS Floriano (Centro)",
    "SAMBAIBA": "UBS Dirceu Arcoverde",
    "SAMBAIBA VELHA": "UBS Dirceu Arcoverde",
    "MANGUINHA": "UBS José Paraguassú",
    "ALTO DA CRUZ": "UBS Theodoro F. Sobral",
    "CAMPO VELHO": "UBS Pedro Simplício",
    "REDE NOVA": "UBS Alfredo de Carvalho",
    "TABOCA": "UBS Luiz Tavares",
    "IRAPUA I": "UBS Camilo Filho",
    "IRAPUA II": "UBS Camilo Filho",
    "NOSSA SENHORA DA GUIA": "UBS N. Sra. da Guia",
    "TIBERAO": "UBS Raimundo Filho",
    "BOM LUGAR": "UBS Paulo Kalume",
    "BOSQUE SANTA TEREZINHA": "UBS João Elias Oka",
    "CAIXA D AGUA": "UBS Theodoro F. Sobral",
    "CAJUEIRO": "UBS João Elias Oka",
    "ALTO DA GUIA": "UBS N. Sra. da Guia",
    "CURADOR": "UBS Theodoro F. Sobral",
    "IBIAPABA": "UBS Viana de Carvalho",
    "PAU FERRADO": "UBS Paulo Martins",
    "SAO BORJA": "UBS Pedro Simplício",
    "PLANALTO SAMBAIBA": "UBS Dirceu Arcoverde",
    "CATUMBI": "UBS Raimundo Filho",
    "SAO CRISTOVAO": "UBS Floriano (Centro)",
    "TAMBORIL": "UBS Alfredo de Carvalho",
    "CONJUNTO PARAISO": "UBS Jasmina Bucar",
    "CANCELA": "UBS Paulo Kalume",
    "CANOAS": "UBS José Paraguassú",
    "PLANALTO BELA VISTA": "UBS Pedro Simplício",
    "MELADAO": "UBS Pedro Simplício",
    "VIAZUL": "UBS Raimundo Filho",
    "PEDRO SIMPLICIO": "UBS Pedro Simplício",
}

UBS_NOME_PARA_CNES = {
    "UBS Theodoro F. Sobral": "2778319",
    "UBS Floriano (Centro)": "2778432",
    "UBS Dirceu Arcoverde": "2778041",
    "UBS José Paraguassú": "5459583",
    "UBS Pedro Simplício": "2778254",
    "UBS Alfredo de Carvalho": "5943817",
    "UBS Luiz Tavares": "2364654",
    "UBS Camilo Filho": "2777916",
    "UBS N. Sra. da Guia": "2364670",
    "UBS Raimundo Filho": "2364697",
    "UBS Paulo Kalume": "2778246",
    "UBS João Elias Oka": "2364689",
    "UBS Viana de Carvalho": "2778335",
    "UBS Paulo Martins": "2609630",
    "UBS Jasmina Bucar": "2995395",
    "UBS do PAM": "2364611",
    "UBS Amolar": "2777843",
    "UBS Helvidio H. Barros": "2778157",
    "UBS L3": "2364638",
    "UBS Leonardo Dudima": "2778181",
    "UBS Margarida Alves Almeida": "2669129",
    "UBS Morrinhos": "2364662",
    "UBS Protasio de Moraes Barbosa": "2778289",
    "UBS Santa Cruz": "2778092",
    "UBS VEREDA GRANDE II": "2364646",
}

UNIDADE_NOTIFICADORA_PARA_UBS = {
    "2320498": "2778432",
    "7654321": "2778254",
    "8765432": "2364689",
    "3036200": "2364689",
    "2365146": "2778432",
    "6137504": "2778157",
    "5005671": "2778432",
    "HOSPITAL TIBERIO NUNES": "2778432",
    "HOSPITAL REGIONAL TIBERIO NUNES": "2778432",
    "HOSPITAL JOAO PAULO II": "2778157",
    "HOSPITAL REGIONAL JOAO PAULO II": "2778157",
    "CAPS ALCOOL E DROGAS": "2778254",
    "CAPS AD": "2778254",
    "CAPS II": "2364689",
    "CENTRO DE HANSENIASE E TUBERCULOSE DE FLORIANO": "2778432",
    "CTA": "2778432",
    "CLINICOR": "2364689",
    "HOSPITAL CLINICOR": "2364689",
    "UPA": "2778335",
    "UPA 24H DR. ADELMAR PEREIRA": "2778335",
    "UPA ADELMAR PEREIRA": "2778335",
    "UPA DR. ADELMAR PEREIRA": "2778335",
    "UPA DR ADELMAR PEREIRA": "2778335",
    "UBS CAMILO FILHO": "2777916",
    "UBS FLORIANO": "2778432",
    "UBS DIRCEU ARCOVERDE": "2778041",
    "UBS DO PAM": "2364611",
    "PAM": "2364611",
    "UBS HELVIDIO DE HOLANDA BARROS": "2778157",
    "UBS HELVIDIO": "2778157",
    "UBS JASMINA BUCAR": "2995395",
    "UBS JOAO ELIAS OKA": "2364689",
    "UBS JOSE PARAGUASU": "5459583",
    "UBS JOSE PARAGUASSU": "5459583",
    "UBS L3": "2364638",
    "UBS LEONARDO DUDIMA": "2778181",
    "UBS LUIZ TAVARES": "2364654",
    "UBS MARGARIDA ALVES": "2669129",
    "UBS MARGARIDA ALVES DE ALMEIDA": "2669129",
    "UBS MORRINHOS": "2364662",
    "UBS NOSSA SENHORA DA GUIA": "2364670",
    "UBS PAULO KALUME": "2778246",
    "UBS PAULO MARTINS": "2609630",
    "UBS PEDRO SIMPLICIO": "2778254",
    "UBS PROTASIO DE MORAES": "2778289",
    "UBS RAIMUNDO FILHO": "2364697",
    "UBS SANTA CRUZ": "2778092",
    "UBS THEODORO": "2778319",
    "UBS THEODORO FERREIRA SOBRAL": "2778319",
    "UBS VEREDA GRANDE": "2364646",
    "UBS VEREDA GRANDE II": "2364646",
    "UBS VIANA CARVALHO": "2778335",
    "UBS VIANA DE CARVALHO": "2778335",
}


def normalizar_texto(texto):
    if texto is None:
        return ""
    return (
        unicodedata.normalize('NFKD', str(texto))
        .encode('ASCII', 'ignore')
        .decode('utf-8')
        .upper()
        .strip()
    )


def extrair_bairro(endereco_string):
    if not endereco_string:
        return None
    # ✅ CORREÇÃO: Força a conversão para string antes de usar o .split()
    end_str = str(endereco_string).strip()
    if not end_str:
        return None

    partes = [p.strip() for p in end_str.split(",") if p.strip()]
    if not partes:
        return None

    ultima = partes[-1]
    eh_cep = (ultima.isdigit() or
              (ultima.replace("-", "").replace(".", "").isdigit()
               and len(ultima) <= 10))
    bairro_bruto = partes[-2] if (eh_cep and len(partes) >= 2) else partes[-1]
    return normalizar_texto(bairro_bruto)


DATA_SENTINELA_INVALIDA = {
    "30/12/1899", "31/12/1899",
    "1899-12-30", "1899-12-31",
    "18991230", "18991231",
    "0000-00-00", "00000000",
}


def _parse_data_full(valor):
    if valor is None:
        return None
    if hasattr(valor, "year") and hasattr(valor, "month") and hasattr(valor, "day"):
        try:
            d = date(int(valor.year), int(valor.month), int(valor.day))
        except (ValueError, AttributeError, TypeError):
            return None
        if d.year == 0:
            return None
        if d.year == 1899 and d.month == 12 and d.day in (30, 31):
            return None
        return d

    s = str(valor).strip()
    if not s or s.lower() in ("nat", "nan", "null", "none"):
        return None
    s = s.split(" ")[0]
    if s in DATA_SENTINELA_INVALIDA:
        return None

    if len(s) == 8 and s.isdigit():
        try:
            d = date(int(s[0:4]), int(s[4:6]), int(s[6:8]))
        except ValueError:
            return None
        if d.year == 0 or (d.year == 1899 and d.month == 12 and d.day in (30, 31)):
            return None
        return d

    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            return None

    if len(s) == 10 and s[2] == "/" and s[5] == "/":
        try:
            return datetime.strptime(s, "%d/%m/%Y").date()
        except ValueError:
            pass

    for fmt in ("%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue

    return None


def _parse_ano(valor):
    if valor is None:
        return None
    if hasattr(valor, "year"):
        try:
            ano = int(valor.year)
            return ano if 1900 <= ano <= 2100 else None
        except (ValueError, TypeError):
            return None

    s = str(valor).strip()
    if not s or s.lower() in ("nat", "nan", "null", "none"):
        return None
    if s.endswith(".0"):
        s = s[:-2]
    if len(s) >= 4 and s[:4].isdigit():
        ano = int(s[:4])
        if 1900 <= ano <= 2100:
            return ano
    return None


def parse_data_com_precisao(valor, fallback_ano=None):
    d = _parse_data_full(valor)
    if d is not None:
        return d.strftime("%Y-%m-%d"), "D"

    if fallback_ano is not None:
        try:
            ano = int(fallback_ano)
            if 1900 <= ano <= 2100:
                return f"{ano:04d}-01-01", "Y"
        except (ValueError, TypeError):
            pass

    return None, "N"


def formatar_data(valor_data):
    d = _parse_data_full(valor_data)
    return d.strftime("%Y-%m-%d") if d else None


def _get(record, *keys):
    """Busca o valor em múltiplas chaves possíveis (SINAN, Django, DBF truncado)."""
    for k in keys:
        if k in record and record[k] is not None and str(record[k]).strip() != "":
            return record[k]
    return None


def processar_registros(records, nome_arquivo, cnes_permitido=None):
    nome_arquivo = nome_arquivo.lower()
    modelo_alvo = None

    for chave, modelo in MAPEA_ENDEMIAS.items():
        if chave in nome_arquivo:
            modelo_alvo = modelo
            break

    if not modelo_alvo:
        return {"status": "erro", "mensagem": "Endemia não reconhecida pelo nome do arquivo."}

    def _montar_endereco(record):
        end_direto = _get(record, 'ENDERECO')
        if end_direto:
            # ✅ CORREÇÃO: Força conversão para string
            return str(end_direto).strip()

        partes = [
            _get(record, 'NM_LOGRADO'), _get(record, 'NM_NUMERO'),
            _get(record, 'NM_COMPLEM'), _get(record, 'NM_BAIRRO'),
            _get(record, 'NU_CEP'),
        ]
        return ", ".join(str(p).strip() for p in partes if p and str(p).strip())

    def _limpar_cnes(valor):
        if valor is None:
            return None
        s = str(valor).strip()
        if s.endswith('.0'):
            s = s[:-2]
        if s.lower() in ('none', 'nan', 'null', ''):
            return None
        return s

    def resolver_id_unidade(record):
        # 1. Bairro de RESIDÊNCIA
        bairro = extrair_bairro(_montar_endereco(record))
        if bairro:
            nome_ubs = BAIRRO_PARA_UBS_NOME.get(bairro)
            if nome_ubs:
                cnes = UBS_NOME_PARA_CNES.get(nome_ubs)
                if cnes and cnes != 'CNES_AQUI':
                    return cnes
            print(f"[AVISO] Bairro não mapeado: {bairro!r}")

        # 2. ID_UNIDADE (hospital, CAPS, etc.)
        valor = _get(record, 'ID_UNIDADE', 'ID_UNID')
        id_original = _limpar_cnes(valor)

        if id_original:
            if id_original in UNIDADE_NOTIFICADORA_PARA_UBS:
                return UNIDADE_NOTIFICADORA_PARA_UBS[id_original]
            id_normalizado = normalizar_texto(id_original)
            if id_normalizado in UNIDADE_NOTIFICADORA_PARA_UBS:
                return UNIDADE_NOTIFICADORA_PARA_UBS[id_normalizado]

        # 3. NM_UBS
        nm_ubs_raw = _get(record, 'NM_UBS', 'NOME_UBS', 'HOSPITAL')
        if nm_ubs_raw:
            chave_nome = normalizar_texto(nm_ubs_raw)
            if chave_nome in UNIDADE_NOTIFICADORA_PARA_UBS:
                return UNIDADE_NOTIFICADORA_PARA_UBS[chave_nome]

        # 4. Fallback
        return id_original

    registros_para_salvar = []
    registros_ignorados = 0

    for record in records:
        id_unidade = resolver_id_unidade(record)

        if cnes_permitido and str(id_unidade).strip() != str(cnes_permitido).strip():
            registros_ignorados += 1
            continue

        if modelo_alvo == PacienteDengue:
            ano_notif = _parse_ano(_get(record, 'NU_ANO', 'SEM_NOT', 'ANO_NOTIFIC', 'ANO_NOTIF'))
            ano_sint = _parse_ano(_get(record, 'SEM_PRI'))

            d_not, p_not = parse_data_com_precisao(_get(record, 'DT_NOTIFIC', 'DATA_NOTIFICACAO', 'DATA_NOTIF'),
                                                   ano_notif)
            p_not_imp = _get(record, 'DATA_NOTIFICACAO_PRECISAO', 'DATA_NOTIFICA_PRECISAO')
            if p_not_imp: p_not = p_not_imp

            d_sin, p_sin = parse_data_com_precisao(_get(record, 'DT_SIN_PRI', 'DATA_PRI_SINTOMA', 'DATA_PRI_S'),
                                                   ano_sint)
            p_sin_imp = _get(record, 'DATA_PRI_SINTOMA_PRECISAO', 'DATA_PRI_SINTO_PRECISAO')
            if p_sin_imp: p_sin = p_sin_imp

            d_nas, p_nas = parse_data_com_precisao(_get(record, 'DT_NASC', 'DATA_NASCIMENTO', 'DATA_NASCI'), None)
            p_nas_imp = _get(record, 'DATA_NASCIMENTO_PRECISAO', 'DATA_NASCI_PRECISAO')
            if p_nas_imp: p_nas = p_nas_imp

            nova_linha = PacienteDengue(
                numero_notificacao=_get(record, 'NU_NOTIFIC', 'NUMERO_NOTIFICACAO', 'NUMERO_NOT'),
                nome_paciente=_get(record, 'NM_PACIENT', 'NOME_PACIENTE', 'NOME_PACIE'),
                data_notificacao=d_not,
                data_notificacao_precisao=p_not,
                data_pri_sintoma=d_sin,
                data_pri_sintoma_precisao=p_sin,
                data_nascimento=d_nas,
                data_nascimento_precisao=p_nas,
                endereco=_montar_endereco(record),
                id_agravo=_get(record, 'ID_AGRAVO'),
                id_unidade=id_unidade,
                hospital=_get(record, 'HOSPITAL'),
                cs_sexo=_get(record, 'CS_SEXO'),
                classi_fin=_get(record, 'CLASSI_FIN'),
            )
        elif modelo_alvo == PacienteTuberculose:
            nova_linha = PacienteTuberculose(
                id_unidade=id_unidade,
                nm_ubs=_get(record, 'NM_UBS', 'NOME_UBS'),
                nu_notific=_get(record, 'NU_NOTIFIC', 'NU_NOTIFICA', 'NUMERO_NOTIFICACAO', 'NUMERO_NOT'),
                ano_notific=_get(record, 'ANO_NOTIFIC', 'NU_ANO', 'ANO_NOTIF'),
            )
        elif modelo_alvo == PacienteSifilis:
            ano_notif = _parse_ano(_get(record, 'NU_ANO', 'ANO_NOTIFIC', 'ANO_NOTIF'))
            d_not, p_not = parse_data_com_precisao(_get(record, 'DT_NOTIFIC', 'DATA_NOTIFICACAO', 'DATA_NOTIF'),
                                                   ano_notif)
            p_not_imp = _get(record, 'DATA_NOTIFICACAO_PRECISAO', 'DATA_NOTIFICA_PRECISAO')
            if p_not_imp: p_not = p_not_imp

            nova_linha = PacienteSifilis(
                id_unidade=id_unidade,
                un_saude=_get(record, 'UN_SADE', 'UN_SAUDE'),
                nm_ubs=_get(record, 'NM_UBS', 'NOME_UBS'),
                mu_residen=_get(record, 'MU_RESIDEN', 'MUNICIPIO_RESIDENCIA'),
                nu_notific=_get(record, 'NU_NOTIFIC', 'NUMERO_NOTIFICACAO', 'NUMERO_NOT'),
                data_notificacao=d_not,
                data_notificacao_precisao=p_not,
                id_agravo=_get(record, 'ID_AGRAVO'),
                nm_pacient=_get(record, 'NM_PACIENT', 'NOME_PACIENTE', 'NOME_PACIE'),
                ano_notific=_get(record, 'ANO_NOTIFIC', 'NU_ANO', 'ANO_NOTIF'),
            )
        elif modelo_alvo == PacienteChagas:
            nova_linha = PacienteChagas(
                id_unidade=id_unidade,
                nm_ubs=_get(record, 'NM_UBS', 'NOME_UBS'),
                nu_notific=_get(record, 'NU_NOTIFIC', 'NU_NOTIFICA', 'NUMERO_NOTIFICACAO', 'NUMERO_NOT'),
                ano_notific=_get(record, 'ANO_NOTIFIC', 'NU_ANO', 'ANO_NOTIF'),
            )
        elif modelo_alvo == PacienteViolenciaDomestica:
            nova_linha = PacienteViolenciaDomestica(
                id_unidade=id_unidade,
                nm_ubs=_get(record, 'NM_UBS', 'NOME_UBS'),
                nu_notific=_get(record, 'NU_NOTIFIC', 'NUMERO_NOTIFICACAO', 'NUMERO_NOT'),
                ano_notific=_get(record, 'ANO_NOTIFIC', 'NU_ANO', 'ANO_NOTIF'),
            )
        elif modelo_alvo == PacienteHans:
            nova_linha = PacienteHans(
                id_unidade=id_unidade,
                nm_ubs=_get(record, 'NM_UBS', 'NOME_UBS'),
                nu_notific=_get(record, 'NU_NOTIFIC', 'NU_NOTIFICA', 'NUMERO_NOTIFICACAO', 'NUMERO_NOT'),
                ano_notific=_get(record, 'ANO_NOTIFIC', 'NU_ANO', 'ANO_NOTIF'),
            )
        elif modelo_alvo == PacienteHepatite:
            nova_linha = PacienteHepatite(
                id_unidade=id_unidade,
                nm_ubs=_get(record, 'NM_UBS', 'NOME_UBS'),
                hospital=_get(record, 'HOSPITAL'),
                ano_notific=_get(record, 'ANO_NOTIFIC', 'NU_ANO', 'ANO_NOTIF'),
                nu_notific=_get(record, 'NU_NOTIFIC', 'NU_NOTIFICA', 'NUMERO_NOTIFICACAO', 'NUMERO_NOT'),
            )
        elif modelo_alvo == PacienteAnimaisPec:
            nova_linha = PacienteAnimaisPec(
                id_unidade=id_unidade,
                nm_ubs=_get(record, 'NM_UBS', 'NOME_UBS'),
                hospital=_get(record, 'HOSPITAL'),
                ano_notific=_get(record, 'ANO_NOTIFIC', 'NU_ANO', 'ANO_NOTIF'),
                nu_notific=_get(record, 'NU_NOTIFIC', 'NU_NOTIFICA', 'NUMERO_NOTIFICACAO', 'NUMERO_NOT'),
            )
        elif modelo_alvo == PacienteIntoxicacao:
            nova_linha = PacienteIntoxicacao(
                id_unidade=id_unidade,
                nm_ubs=_get(record, 'NM_UBS', 'NOME_UBS'),
                hospital=_get(record, 'HOSPITAL'),
                ano_notific=_get(record, 'ANO_NOTIFIC', 'NU_ANO', 'ANO_NOTIF'),
                nu_notific=_get(record, 'NU_NOTIFIC', 'NUMERO_NOTIFICACAO', 'NUMERO_NOT'),
            )
        elif modelo_alvo == PacienteLeish:
            nova_linha = PacienteLeish(
                id_unidade=id_unidade,
                nm_ubs=_get(record, 'NM_UBS', 'NOME_UBS'),
                hospital=_get(record, 'HOSPITAL'),
                ano_notific=_get(record, 'ANO_NOTIFIC', 'NU_ANO', 'ANO_NOTIF'),
                nu_notific=_get(record, 'NU_NOTIFIC', 'NUMERO_NOTIFICACAO', 'NUMERO_NOT'),
            )
        elif modelo_alvo == PacienteAidsAdulto:
            nova_linha = PacienteAidsAdulto(
                id_unidade=id_unidade,
                nm_ubs=_get(record, 'NM_UBS', 'NOME_UBS'),
                hospital=_get(record, 'HOSPITAL'),
                ano_notific=_get(record, 'ANO_NOTIFIC', 'NU_ANO', 'ANO_NOTIF'),
                nu_notific=_get(record, 'NU_NOTIFIC', 'NUMERO_NOTIFICACAO', 'NUMERO_NOT'),
            )
        elif modelo_alvo == CoberturaVacinal:
            nova_linha = CoberturaVacinal(
                ano=_parse_ano(_get(record, 'ANO', 'NU_ANO')) or 0,
                imunobiologico=_get(record, 'IMUNOBIOLOGICO', 'VACINA') or '',
                cobertura_percentual=float(_get(record, 'COBERTURA_PERCENTUAL', 'COBERTURA') or 0.0),
                meta_otima=float(_get(record, 'META_OTIMA', 'META') or 95.0),
            )
        else:
            continue

        registros_para_salvar.append(nova_linha)

    modelo_alvo.objects.bulk_create(registros_para_salvar, ignore_conflicts=True)
    return {
        "status": "sucesso",
        "registros_inseridos": len(registros_para_salvar),
        "registros_ignorados": registros_ignorados,
    }


def processar_arquivo_dbf(caminho_arquivo, nome_original=None, cnes_permitido=None):
    nome_arquivo = (nome_original or os.path.basename(caminho_arquivo)).lower()
    tabela = DBF(caminho_arquivo, encoding='iso-8859-1', load=True, ignore_missing_memofile=True)
    return processar_registros(list(tabela), nome_arquivo, cnes_permitido=cnes_permitido)