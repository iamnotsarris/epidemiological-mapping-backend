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


def processar_registros(records, nome_arquivo):
    """Recebe uma lista de dicionários (do DBF ou do Excel) e salva no banco."""
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
            # Se já vier como datetime/Timestamp (Excel)
            if hasattr(valor_data, "strftime"):
                return valor_data.strftime("%Y-%m-%d")

            # Se vier como string
            data_limpa = str(valor_data).strip().split(" ")[0]
            if data_limpa in ("30/12/1899", "NaT", "nan", ""):
                return None

            # Tenta DD/MM/YYYY primeiro
            try:
                return datetime.strptime(data_limpa, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                pass

            # Tenta YYYY-MM-DD (formato que o pandas às vezes entrega)
            try:
                return datetime.strptime(data_limpa, "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError:
                pass

            return None
        except (ValueError, TypeError, AttributeError):
            return None

    registros_para_salvar = []

    for record in records:
        if modelo_alvo == PacienteDengue:
            partes_endereco = [
                record.get('NM_LOGRADO'),
                record.get('NM_NUMERO'),
                record.get('NM_COMPLEM'),
                record.get('NM_BAIRRO'),
                record.get('NU_CEP'),
            ]
            partes_validadas = [str(p).strip() for p in partes_endereco if p and str(p).strip()]
            endereco_formatado = ", ".join(partes_validadas)

            nova_linha = PacienteDengue(
                numero_notificacao=record.get('NU_NOTIFIC'),
                nome_paciente=record.get('NM_PACIENT'),
                data_notificacao=formatar_data(record.get('DT_NOTIFIC')),
                data_pri_sintoma=formatar_data(record.get('DT_SIN_PRI')),
                data_nascimento=formatar_data(record.get('DT_NASC')),
                endereco=endereco_formatado,
                id_agravo=record.get('ID_AGRAVO'),
                id_unidade=record.get('ID_UNIDADE'),
                hospital=record.get('HOSPITAL'),
                cs_sexo=record.get('CS_SEXO'),
                classi_fin=record.get('CLASSI_FIN'),
            )
            registros_para_salvar.append(nova_linha)

        elif modelo_alvo == PacienteTuberculose:
            nova_linha = PacienteTuberculose(
                id_unidade=record.get('ID_UNIDADE') or record.get('ID_UNID'),
                nm_ubs=record.get('NM_UBS') or record.get('ID_UNIDADE'),
                nu_notific=record.get('NU_NOTIFIC') or record.get('NU_NOTIFICA'),
                ano_notific=record.get('ANO_NOTIFIC'),
            )
            registros_para_salvar.append(nova_linha)

        elif modelo_alvo == PacienteSifilis:
            nova_linha = PacienteSifilis(
                mu_notific=record.get('MU_NOTIFIC'),
                un_saude=record.get('UN_SAUDE'),
                nu_notific=record.get('NU_NOTIFIC'),
                dt_notific=formatar_data(record.get('DT_NOTIFIC')),
                id_agravo=record.get('ID_AGRAVO'),
                nm_pacient=record.get('NM_PACIENT'),
                nm_ubs=record.get('NM_UBS'),
                ano_notific=record.get('ANO_NOTIFIC'),
            )
            registros_para_salvar.append(nova_linha)

        elif modelo_alvo == PacienteViolenciaDomestica:
            nova_linha = PacienteViolenciaDomestica(
                id_unidade=record.get('ID_UNIDADE'),
                nm_ubs=record.get('NM_UBS'),
                nu_notific=record.get('NU_NOTIFIC'),
                ano_notific=record.get('ANO_NOTIFIC'),
            )
            registros_para_salvar.append(nova_linha)

        elif modelo_alvo == PacienteChagas:
            nova_linha = PacienteChagas(
                id_unidade=record.get('ID_UNIDADE'),
                nm_ubs=record.get('NM_UBS'),
                nu_notific=record.get('NU_NOTIFIC'),
                ano_notific=record.get('ANO_NOTIFIC'),
            )
            registros_para_salvar.append(nova_linha)

        elif modelo_alvo == PacienteHans:
            nova_linha = PacienteHans(
                id_unidade=record.get('ID_UNIDADE'),
                nm_ubs=record.get('NM_UBS'),
                nu_notific=record.get('NU_NOTIFIC'),
                ano_notific=record.get('ANO_NOTIFIC'),
            )
            registros_para_salvar.append(nova_linha)

        elif modelo_alvo == PacienteHepatite:
            nova_linha = PacienteHepatite(
                id_unidade=record.get('ID_UNIDADE'),
                nm_ubs=record.get('NM_UBS'),
                nu_notific=record.get('NU_NOTIFIC'),
                ano_notific=record.get('ANO_NOTIFIC'),
            )
            registros_para_salvar.append(nova_linha)

        elif modelo_alvo == PacienteAnimaisPec:
            nova_linha = PacienteAnimaisPec(
                id_unidade=record.get('ID_UNIDADE'),
                nm_ubs=record.get('NM_UBS'),
                nu_notific=record.get('NU_NOTIFIC'),
                hospital=record.get('HOSPITAL'),
                ano_notific=record.get('ANO_NOTIFIC'),
            )
            registros_para_salvar.append(nova_linha)

        elif modelo_alvo == PacienteIntoxicacao:
            nova_linha = PacienteIntoxicacao(
                ano_notific=record.get('ANO_NOTIFIC'),
                nu_notific=record.get('NU_NOTIFIC'),
            )
            registros_para_salvar.append(nova_linha)

        elif modelo_alvo == PacienteLeish:
            nova_linha = PacienteLeish(
                ano_notific=record.get('ANO_NOTIFIC'),
                nu_notific=record.get('NU_NOTIFIC'),
            )
            registros_para_salvar.append(nova_linha)

        elif modelo_alvo == PacienteAidsAdulto:
            nova_linha = PacienteAidsAdulto(
                ano_notific=record.get('ANO_NOTIFIC'),
                nu_notific=record.get('NU_NOTIFIC'),
            )
            registros_para_salvar.append(nova_linha)

        elif modelo_alvo == CoberturaVacinal:
            nova_linha = CoberturaVacinal(
                ano=record.get('ANO'),
                imunobiologico=record.get('IMUNOBIOLOGICO'),
                cobertura_percentual=record.get('COBERTURA_PERCENTUAL'),
                meta_otima=record.get('META_OTIMA'),
                data_atualizacao=record.get('DATA_ATUALIZACAO'),
                # ⚠️ ano_notific NÃO existe no model CoberturaVacinal
            )
            registros_para_salvar.append(nova_linha)

    modelo_alvo.objects.bulk_create(registros_para_salvar, ignore_conflicts=True)
    return {"status": "sucesso", "registros_inseridos": len(registros_para_salvar)}


def processar_arquivo_dbf(caminho_arquivo, nome_original=None):
    nome_arquivo = (nome_original or os.path.basename(caminho_arquivo)).lower()
    tabela = DBF(caminho_arquivo, encoding='iso-8859-1', load=True, ignore_missing_memofile=True)
    return processar_registros(list(tabela), nome_arquivo)