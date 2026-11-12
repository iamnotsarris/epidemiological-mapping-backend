# api/utils/gerador_pdf.py
import io
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.db.models import Count, Sum, IntegerField
from django.db.models.functions import Trim, Upper, Cast
from api.models import PacienteDengue
from api.utils.assistente import DOENCAS, _normalizar_doenca


def _get_campo_notificacao(modelo):
    """Retorna o nome do campo que identifica a notificação no modelo."""
    for campo in ['nu_notific', 'numero_notificacao']:
        try:
            modelo._meta.get_field(campo)
            return campo
        except Exception:
            pass
    return None


def _calcular_total_casos(qs, modelo):
    """
    Soma o valor do campo de notificação (ex: 95 + 3 + 19 + 1 = 118).
    Se o campo não for numérico, faz a contagem padrão (distinct).
    """
    campo = _get_campo_notificacao(modelo)
    if campo:
        qs_valido = qs.exclude(**{f"{campo}__isnull": True}).exclude(**{campo: ''})
        try:
            # Tenta converter para inteiro e somar
            total_soma = qs_valido.annotate(
                valor_int=Cast(campo, IntegerField())
            ).aggregate(total=Sum('valor_int'))['total']

            if total_soma is not None:
                return total_soma
        except Exception:
            # Fallback: se houver letras no campo, conta as notificações únicas
            return qs_valido.annotate(
                _notific_limpa=Upper(Trim(campo))
            ).exclude(_notific_limpa='').values('_notific_limpa').distinct().count()

    return qs.count()


def gerar_relatorio_mensal(mes=None, ano=None, agravo='geral'):
    MESES_NOMES = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro",
                   "Outubro", "Novembro", "Dezembro"]

    if mes and int(mes) > 0:
        mes = int(mes)
        periodo = f"{MESES_NOMES[mes]}/{ano}"
    else:
        mes = None
        periodo = f"Anual/{ano}"

    context = {
        "ano": ano,
        "agravo": agravo,
        "periodo": periodo
    }

    if agravo == 'geral':
        totais_gerais = {}

        for chave, info in DOENCAS.items():
            modelo = info['modelo']
            campo_ano = info['campo_ano']

            qs = modelo.objects.all()

            if 'data_notificacao' in campo_ano:
                qs = qs.filter(data_notificacao__year=ano)
                if mes:
                    qs = qs.filter(data_notificacao__month=mes)
            else:
                qs = qs.filter(**{campo_ano: str(ano)})

            totais_gerais[chave] = _calcular_total_casos(qs, modelo)

        # Dengue por UBS
        qs_dengue = PacienteDengue.objects.filter(data_notificacao__year=ano)
        if mes:
            qs_dengue = qs_dengue.filter(data_notificacao__month=mes)

        qs_dengue_validas = qs_dengue.exclude(numero_notificacao__isnull=True).exclude(numero_notificacao='')

        try:
            agravos_ubs = qs_dengue_validas.values('id_unidade').annotate(
                dengue_count=Sum(Cast('numero_notificacao', IntegerField()))
            ).order_by('-dengue_count')[:10]
        except Exception:
            agravos_ubs = qs_dengue_validas.annotate(
                _notific_limpa=Upper(Trim('numero_notificacao'))
            ).exclude(_notific_limpa='').values('id_unidade').annotate(
                dengue_count=Count('_notific_limpa', distinct=True)
            ).order_by('-dengue_count')[:10]

        context.update({
            "totais_gerais": totais_gerais,
            "agravos_ubs": agravos_ubs
        })

    else:
        chave = _normalizar_doenca(agravo)
        info = DOENCAS.get(chave)

        if not info:
            raise Exception(f"Agravo '{agravo}' não encontrado.")

        modelo = info['modelo']
        campo_ano = info['campo_ano']
        campo_ubs = info['campo_ubs']

        qs = modelo.objects.all()

        if 'data_notificacao' in campo_ano:
            qs = qs.filter(data_notificacao__year=ano)
            if mes:
                qs = qs.filter(data_notificacao__month=mes)
        else:
            qs = qs.filter(**{campo_ano: str(ano)})

        total_casos = _calcular_total_casos(qs, modelo)

        campo_notificacao = _get_campo_notificacao(modelo)
        if campo_notificacao:
            qs_validas = qs.exclude(**{f"{campo_notificacao}__isnull": True}).exclude(**{campo_notificacao: ''})
            try:
                # Soma a quantidade de casos agrupados por UBS
                agravos_ubs = qs_validas.values(campo_ubs).annotate(
                    total=Sum(Cast(campo_notificacao, IntegerField()))
                ).order_by('-total')[:15]
            except Exception:
                # Fallback se houver letras
                qs_texto = qs_validas.annotate(
                    _notific_limpa=Upper(Trim(campo_notificacao))
                ).exclude(_notific_limpa='')
                agravos_ubs = qs_texto.values(campo_ubs).annotate(
                    total=Count('_notific_limpa', distinct=True)
                ).order_by('-total')[:15]
        else:
            agravos_ubs = qs.values(campo_ubs).annotate(
                total=Count('id')
            ).order_by('-total')[:15]

        bairros = []
        if chave == 'dengue':
            from api.utils.importador_dbf import extrair_bairro
            contagem = {}
            for endereco, num_not in qs.exclude(endereco__isnull=True).exclude(endereco='').exclude(
                    numero_notificacao__isnull=True).exclude(numero_notificacao='').values_list('endereco',
                                                                                                'numero_notificacao').distinct().iterator():
                b = extrair_bairro(endereco)
                if b:
                    contagem[b] = contagem.get(b, 0) + 1
            bairros = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:10]

        context.update({
            "agravo_nome": chave.capitalize(),
            "total_casos": total_casos,
            "agravos_ubs": agravos_ubs,
            "campo_ubs": campo_ubs.replace('_', ' ').title(),
            "bairros": bairros
        })

    html_string = render_to_string('relatorios/mensal.html', context)
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(html_string.encode("UTF-8")), dest=pdf_buffer)

    if pisa_status.err:
        raise Exception("Erro ao gerar PDF com xhtml2pdf")

    return pdf_buffer.getvalue()