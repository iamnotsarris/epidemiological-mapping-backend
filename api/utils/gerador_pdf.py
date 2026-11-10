# api/utils/gerador_pdf.py
import io
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.db.models import Count
from api.models import PacienteDengue, PacienteSifilis, PacienteTuberculose, CoberturaVacinal


def gerar_relatorio_mensal(mes, ano):
    MESES_NOMES = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro",
                   "Outubro", "Novembro", "Dezembro"]

    # 1. Busca dados para os KPIs
    kpis = {
        "dengue": PacienteDengue.objects.filter(data_notificacao__month=mes, data_notificacao__year=ano).count(),
        "sifilis": PacienteSifilis.objects.filter(data_notificacao__month=mes, data_notificacao__year=ano).count(),
        "tuberculose": PacienteTuberculose.objects.filter(ano_notific=str(ano)).count(),
    }

    # 2. Busca Vacinas
    vacinas = CoberturaVacinal.objects.filter(ano=ano).order_by('imunobiologico')

    # 3. Agrupamento por UBS
    agravos_ubs = PacienteDengue.objects.filter(
        data_notificacao__month=mes, data_notificacao__year=ano
    ).values('id_unidade').annotate(
        dengue_count=Count('id')
    ).order_by('-dengue_count')[:10]

    # 4. Monta o Contexto
    context = {
        "mes": mes,
        "mes_nome": MESES_NOMES[mes],
        "ano": ano,
        "kpis": kpis,
        "vacinas": vacinas,
        "agravos_ubs": agravos_ubs,
    }

    # 5. Renderiza HTML e converte para PDF
    html_string = render_to_string('relatorios/mensal.html', context)

    # GERA O PDF COM XHTML2PDF
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        io.BytesIO(html_string.encode("UTF-8")),
        dest=pdf_buffer
    )

    if pisa_status.err:
        raise Exception("Erro ao gerar PDF com xhtml2pdf")

    return pdf_buffer.getvalue()