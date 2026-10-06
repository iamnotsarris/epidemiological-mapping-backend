import os
from api.models import (
    PacienteDengue, PacienteTuberculose, PacienteSifilis, PacienteViolenciaDomestica,
    PacienteChagas, PacienteHans, PacienteHepatite, PacienteAnimaisPec,
    PacienteIntoxicacao, PacienteLeish, PacienteAidsAdulto, CoberturaVacinal,
)
from dbfread import DBF
from datetime import datetime

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

# 1. MAPEAMENTO DE BAIRRO PARA NOME DA UBS (Baseado no seu Frontend)
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

# 2. MAPEAMENTO DE NOME DA UBS PARA CNES (id_unidade)
# Atualize estes números com os CNES reais do seu banco de dados se não baterem!
UBS_NOME_PARA_CNES = {
    "UBS Theodoro F. Sobral": "2778319",
    "UBS Floriano (Centro)": "2778432",
    # Preencha os demais CNES conforme você criar os usuários UBS no painel:
    "UBS Dirceu Arcoverde": "CNES_AQUI",
    "UBS José Paraguassú": "CNES_AQUI",
    "UBS Pedro Simplício": "CNES_AQUI",
    "UBS Alfredo de Carvalho": "CNES_AQUI",
    "UBS Luiz Tavares": "CNES_AQUI",
    "UBS Camilo Filho": "CNES_AQUI",
    "UBS N. Sra. da Guia": "CNES_AQUI",
    "UBS Raimundo Filho": "CNES_AQUI",
    "UBS Paulo Kalume": "CNES_AQUI",
    "UBS João Elias Oka": "CNES_AQUI",
    "UBS Viana de Carvalho": "CNES_AQUI",
    "UBS Paulo Martins": "CNES_AQUI",
    "UBS Jasmina Bucar": "CNES_AQUI",
}


def extrair_bairro(endereco_string):
    """Tenta extrair e normalizar o nome do bairro do endereço concatenado"""
    if not endereco_string:
        return None

    partes = [p.strip() for p in endereco_string.split(",") if p.strip()]
    if not partes:
        return None

    ultima = partes[-1]

    # Verifica se a última parte é um CEP. Se for, o bairro costuma ser a penúltima parte
    eh_cep = (ultima.isdigit() or
              (ultima.replace("-", "").replace(".", "").isdigit()
               and len(ultima) <= 10))

    bairro_bruto = partes[-2] if (eh_cep and len(partes) >= 2) else partes[-1]

    # Normaliza: Remove acentos e joga pra maiúsculo (importante para bater com o dicionário)
    import unicodedata
    bairro_normalizado = unicodedata.normalize('NFKD', bairro_bruto).encode('ASCII', 'ignore').decode('utf-8').upper()
    return bairro_normalizado


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

    def resolver_id_unidade(record):
        """Pega ID_UNIDADE do DBF ou tenta inferir pelo bairro (só dengue)."""
        valor = record.get('ID_UNIDADE')
        if valor is None:
            valor = record.get('ID_UNID')

        # Converte qualquer tipo (int, float, str, None) para string limpa
        if valor is None:
            id_original = ''
        else:
            id_original = str(valor).strip()
            # Se vier "2778432.0" de float, tira o ".0"
            if id_original.endswith('.0'):
                id_original = id_original[:-2]
            if id_original.lower() in ('none', 'nan', 'null', ''):
                id_original = ''

        if id_original:
            return id_original

        # Fallback: tenta inferir pelo bairro (só faz sentido para dengue)
        bairro = extrair_bairro(_montar_endereco(record))
        if bairro:
            nome_ubs = BAIRRO_PARA_UBS_NOME.get(bairro)
            if nome_ubs:
                cnes = UBS_NOME_PARA_CNES.get(nome_ubs)
                if cnes and cnes != 'CNES_AQUI':
                    return cnes

        return None

    def _montar_endereco(record):
        partes = [
            record.get('NM_LOGRADO'), record.get('NM_NUMERO'),
            record.get('NM_COMPLEM'), record.get('NM_BAIRRO'),
            record.get('NU_CEP'),
        ]
        return ", ".join(str(p).strip() for p in partes if p and str(p).strip())

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