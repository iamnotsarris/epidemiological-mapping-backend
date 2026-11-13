# api/utils/gerador_pdf.py
import io
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.db.models import Count, Sum, IntegerField
from django.db.models.functions import Cast
from api.models import PacienteDengue
from api.utils.assistente import DOENCAS, _normalizar_doenca


def _get_campo_notificacao(modelo):
    """Identifica qual campo de notificação o modelo usa."""
    if hasattr(modelo, 'numero_notificacao'):
        return 'numero_notificacao'  # Usado na Dengue (ID da ficha)
    elif hasattr(modelo, 'nu_notific'):
        return 'nu_notific'  # Usado nas outras (ID ou Quantidade)
    return None


def _calcular_total(qs, campo, chave):
    """Aplica a regra correta dependendo do campo e da doença."""
    if not campo:
        return qs.count()

    qs_valido = qs.exclude(**{f"{campo}__isnull": True}).exclude(**{campo: ''})

    # Doenças onde o campo NU_NOTIFIC é o ID da ficha (devemos contar, não somar)
    doencas_contagem = ['dengue', 'sifilis']

    if chave in doencas_contagem or campo == 'numero_notificacao':
        # Conta IDs únicos (Dengue, Sífilis)
        return qs_valido.values(campo).distinct().count()
    else:
        # Soma os valores (Violência, etc)
        try:
            total = qs_valido.annotate(v_int=Cast(campo, IntegerField())).aggregate(soma=Sum('v_int'))['soma']
            return total or 0
        except Exception:
            # Fallback caso tenha letras no campo
            return qs_valido.values(campo).distinct().count()


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

            campo = _get_campo_notificacao(modelo)
            totais_gerais[chave] = _calcular_total(qs, campo, chave)

        # Dengue por UBS
        qs_dengue = PacienteDengue.objects.filter(data_notificacao__year=ano)
        if mes:
            qs_dengue = qs_dengue.filter(data_notificacao__month=mes)

        qs_dengue_validas = qs_dengue.exclude(numero_notificacao__isnull=True).exclude(numero_notificacao='')

        # Dengue conta IDs únicos
        agravos_ubs = qs_dengue_validas.values('id_unidade').annotate(
            dengue_count=Count('numero_notificacao', distinct=True)
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

        campo_notificacao = _get_campo_notificacao(modelo)
        total_casos = _calcular_total(qs, campo_notificacao, chave)

        if campo_notificacao:
            qs_validas = qs.exclude(**{f"{campo_notificacao}__isnull": True}).exclude(**{campo_notificacao: ''})

            # Mesma regra para agrupar por UBS
            doencas_contagem = ['dengue', 'sifilis']

            if campo_notificacao == 'nu_notific' and chave not in doencas_contagem:
                # Soma os casos por UBS (Violência, etc)
                try:
                    agravos_ubs = qs_validas.values(campo_ubs).annotate(
                        total=Sum(Cast(campo_notificacao, IntegerField()))
                    ).order_by('-total')[:15]
                except Exception:
                    agravos_ubs = qs_validas.values(campo_ubs).annotate(
                        total=Count(campo_notificacao, distinct=True)
                    ).order_by('-total')[:15]
            else:
                # Conta IDs distintos por UBS (Dengue, Sífilis)
                agravos_ubs = qs_validas.values(campo_ubs).annotate(
                    total=Count(campo_notificacao, distinct=True)
                ).order_by('-total')[:15]
        else:
            agravos_ubs = qs.values(campo_ubs).annotate(
                total=Count('id')
            ).order_by('-total')[:15]

        bairros = []
        if chave == 'dengue':
            from api.utils.importador_dbf import extrair_bairro
            contagem = {}
            # Conta IDs únicos por bairro
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