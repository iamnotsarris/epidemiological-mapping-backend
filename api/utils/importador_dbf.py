import os
from api.models import (
    PacienteDengue, PacienteTuberculose, PacienteSifilis, PacienteViolenciaDomestica,
    PacienteChagas, PacienteHans, PacienteHepatite, PacienteAnimaisPec,
    PacienteIntoxicacao, PacienteLeish, PacienteAidsAdulto, CoberturaVacinal,
)
from dbfread import DBF
from datetime import datetime
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

    "HOSPITAL TIBERIO NUNES":   "2778432",
    "HOSPITAL TIBÉRIO NUNES":   "2778432",
    "CAPS ALCOOL E DROGAS":     "2778254",
    "CAPS AD":                  "2778254",
    "CAPS II":                  "2364689",
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
    """Tenta extrair e normalizar o nome do bairro do endereço concatenado"""
    if not endereco_string:
        return None

    partes = [p.strip() for p in endereco_string.split(",") if p.strip()]
    if not partes:
        return None

    ultima = partes[-1]

    eh_cep = (ultima.isdigit() or
              (ultima.replace("-", "").replace(".", "").isdigit()
               and len(ultima) <= 10))

    bairro_bruto = partes[-2] if (eh_cep and len(partes) >= 2) else partes[-1]
    return normalizar_texto(bairro_bruto)


def processar_registros(records, nome_arquivo):
    nome_arquivo = nome_arquivo.lower()
    modelo_alvo = None

    for chave, modelo in MAPEA_ENDEMIAS.items():
        if chave in nome_arquivo:
            modelo_alvo = modelo
            break

    if not modelo_alvo:
        return {"status": "erro", "mensagem": "Endemia não reconhecida pelo nome do arquivo."}

    def formatar_data(valor_data):
        if not valor_data:
            return None
        try:
            if hasattr(valor_data, "strftime"):
                return valor_data.strftime("%Y-%m-%d")
            data_limpa = str(valor_data).strip().split(" ")[0]
            if data_limpa in ("30/12/1899", "NaT", "nan", ""):
                return None
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(data_limpa, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
            return None
        except (ValueError, TypeError, AttributeError):
            return None

    def _montar_endereco(record):
        partes = [
            record.get('NM_LOGRADO'), record.get('NM_NUMERO'),
            record.get('NM_COMPLEM'), record.get('NM_BAIRRO'),
            record.get('NU_CEP'),
        ]
        return ", ".join(str(p).strip() for p in partes if p and str(p).strip())

    def _limpar_cnes(valor):
        """Converte qualquer coisa em string limpa de CNES (sem .0, sem nan)."""
        if valor is None:
            return None
        s = str(valor).strip()
        if s.endswith('.0'):
            s = s[:-2]
        if s.lower() in ('none', 'nan', 'null', ''):
            return None
        return s

    def resolver_id_unidade(record):
        """
        Prioridade:
          1) Bairro de RESIDÊNCIA → UBS do território  (mais correto)
          2) ID_UNIDADE — se for hospital/CAPS conhecido, redireciona p/ UBS do território
             2a) tenta match por CNES
             2b) tenta match por NM_UBS (normalizado)
          3) ID_UNIDADE cru (assume que já é uma UBS)
        """

        bairro = extrair_bairro(_montar_endereco(record))
        if bairro:
            nome_ubs = BAIRRO_PARA_UBS_NOME.get(bairro)
            if nome_ubs:
                cnes = UBS_NOME_PARA_CNES.get(nome_ubs)
                if cnes and cnes != 'CNES_AQUI':
                    return cnes
            print(f"[AVISO] Bairro não mapeado: {bairro!r}")

        valor = record.get('ID_UNIDADE')
        if valor is None:
            valor = record.get('ID_UNID')

        id_original = _limpar_cnes(valor)

        if id_original and id_original in UNIDADE_NOTIFICADORA_PARA_UBS:
            return UNIDADE_NOTIFICADORA_PARA_UBS[id_original]

        nm_ubs_raw = record.get('NM_UBS')
        if nm_ubs_raw:
            chave_nome = normalizar_texto(nm_ubs_raw)
            if chave_nome in UNIDADE_NOTIFICADORA_PARA_UBS:
                return UNIDADE_NOTIFICADORA_PARA_UBS[chave_nome]

        return id_original

    registros_para_salvar = []

    for record in records:
        id_unidade = resolver_id_unidade(record)

        if modelo_alvo == PacienteDengue:
            nova_linha = PacienteDengue(
                numero_notificacao=record.get('NU_NOTIFIC'),
                nome_paciente=record.get('NM_PACIENT'),
                data_notificacao=formatar_data(record.get('DT_NOTIFIC')),
                data_pri_sintoma=formatar_data(record.get('DT_SIN_PRI')),
                data_nascimento=formatar_data(record.get('DT_NASC')),
                endereco=_montar_endereco(record),
                id_agravo=record.get('ID_AGRAVO'),
                id_unidade=id_unidade,
                hospital=record.get('HOSPITAL'),
                cs_sexo=record.get('CS_SEXO'),
                classi_fin=record.get('CLASSI_FIN'),
            )
        elif modelo_alvo == PacienteTuberculose:
            nova_linha = PacienteTuberculose(
                id_unidade=id_unidade,
                nm_ubs=record.get('NM_UBS') or record.get('ID_UNIDADE'),
                nu_notific=record.get('NU_NOTIFIC') or record.get('NU_NOTIFICA'),
                ano_notific=record.get('ANO_NOTIFIC'),
            )
        elif modelo_alvo == PacienteSifilis:
            nova_linha = PacienteSifilis(
                id_unidade=id_unidade,
                un_saude=record.get('UN_SADE'),
                nm_ubs=record.get('NM_UBS'),
                mu_residen=record.get('MU_RESIDEN'),
                nu_notific=record.get('NU_NOTIFIC'),
                dt_notific=formatar_data(record.get('DT_NOTIFIC')),
                id_agravo=record.get('ID_AGRAVO'),
                nm_pacient=record.get('NM_PACIENT'),
                ano_notific=record.get('ANO_NOTIFIC'),
            )
        elif modelo_alvo == PacienteChagas:
            nova_linha = PacienteChagas(
                id_unidade=id_unidade,
                nm_ubs=record.get('NM_UBS'),
                nu_notific=record.get('NU_NOTIFIC') or record.get('NU_NOTIFICA'),
                ano_notific=record.get('ANO_NOTIFIC'),
            )
        elif modelo_alvo == PacienteViolenciaDomestica:
            nova_linha = PacienteViolenciaDomestica(
                id_unidade=id_unidade,
                nm_ubs=record.get('NM_UBS'),
                nu_notific=record.get('NU_NOTIFIC'),
                ano_notific=record.get('ANO_NOTIFIC'),
            )
        elif modelo_alvo == PacienteHans:
            nova_linha = PacienteHans(
                id_unidade=id_unidade,
                nm_ubs=record.get('NM_UBS'),
                nu_notific=record.get('NU_NOTIFIC') or record.get('NU_NOTIFICA'),
                ano_notific=record.get('ANO_NOTIFIC'),
            )
        elif modelo_alvo == PacienteHepatite:
            nova_linha = PacienteHepatite(
                id_unidade=id_unidade,
                nm_ubs=record.get('NM_UBS'),
                nu_notific=record.get('NU_NOTIFIC') or record.get('NU_NOTIFICA'),
                ano_notific=record.get('ANO_NOTIFIC'),
            )
        elif modelo_alvo == PacienteAnimaisPec:
            nova_linha = PacienteAnimaisPec(
                id_unidade=id_unidade,
                nm_ubs=record.get('NM_UBS'),
                hospital=record.get('HOSPITAL'),
                ano_notific=record.get('ANO_NOTIFIC'),
                nu_notific=record.get('NU_NOTIFIC') or record.get('NU_NOTIFICA'),
            )
        elif modelo_alvo == PacienteIntoxicacao:
            nova_linha = PacienteIntoxicacao(
                id_unidade=id_unidade,
                ano_notific=record.get('ANO_NOTIFIC'),
                nu_notific=record.get('NU_NOTIFIC'),
            )
        elif modelo_alvo == PacienteLeish:
            nova_linha = PacienteLeish(
                id_unidade=id_unidade,
                ano_notific=record.get('ANO_NOTIFIC'),
                nu_notific=record.get('NU_NOTIFIC'),
            )
        elif modelo_alvo == PacienteAidsAdulto:
            nova_linha = PacienteAidsAdulto(
                id_unidade=id_unidade,
                ano_notific=record.get('ANO_NOTIFIC'),
                nu_notific=record.get('NU_NOTIFIC'),
            )
        else:
            continue

        registros_para_salvar.append(nova_linha)

    modelo_alvo.objects.bulk_create(registros_para_salvar, ignore_conflicts=True)
    return {"status": "sucesso", "registros_inseridos": len(registros_para_salvar)}


def processar_arquivo_dbf(caminho_arquivo, nome_original=None):
    nome_arquivo = (nome_original or os.path.basename(caminho_arquivo)).lower()
    tabela = DBF(caminho_arquivo, encoding='iso-8859-1', load=True, ignore_missing_memofile=True)
    return processar_registros(list(tabela), nome_arquivo)