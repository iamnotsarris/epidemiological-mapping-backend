# api/utils/gerador_pdf.py
import io
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.db.models import Count
from api.models import PacienteDengue, PacienteSifilis, PacienteTuberculose, CoberturaVacinal
from api.utils.assistente import DOENCAS, _normalizar_doenca


def gerar_relatorio_mensal(mes=None, ano=None, agravo='geral'):
    MESES_NOMES = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro",
                   "Outubro", "Novembro", "Dezembro"]

    # Define o texto do período (Mensal ou Anual)
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
        # --- LÓGICA DO PANORAMA GERAL ---
        qs_dengue = PacienteDengue.objects.filter(data_notificacao__year=ano)
        qs_sifilis = PacienteSifilis.objects.filter(data_notificacao__year=ano)

        # Tuberculose usa ano_notific (texto), então só filtra por ano
        qs_tuberculose = PacienteTuberculose.objects.filter(ano_notific=str(ano))

        if mes:
            qs_dengue = qs_dengue.filter(data_notificacao__month=mes)
            qs_sifilis = qs_sifilis.filter(data_notificacao__month=mes)

        kpis = {
            "dengue": qs_dengue.count(),
            "sifilis": qs_sifilis.count(),
            "tuberculose": qs_tuberculose.count(),
        }

        vacinas = CoberturaVacinal.objects.filter(ano=ano).order_by('imunobiologico')
        agravos_ubs = qs_dengue.values('id_unidade').annotate(dengue_count=Count('id')).order_by('-dengue_count')[:10]

        context.update({"kpis": kpis, "vacinas": vacinas, "agravos_ubs": agravos_ubs})

    else:
        # --- LÓGICA ESPECÍFICA DO AGRAVO ---
        chave = _normalizar_doenca(agravo)
        info = DOENCAS.get(chave)

        if not info:
            raise Exception(f"Agravo '{agravo}' não encontrado.")

        modelo = info['modelo']
        campo_ano = info['campo_ano']
        campo_ubs = info['campo_ubs']

        qs = modelo.objects.all()

        # Filtra apenas pelo ano base
        if 'data_notificacao' in campo_ano:
            qs = qs.filter(data_notificacao__year=ano)
            if mes:
                qs = qs.filter(data_notificacao__month=mes)  # Aplica o mês se existir e for data
        else:
            qs = qs.filter(**{campo_ano: str(ano)})

        total_casos = qs.count()

        agravos_ubs = qs.values(campo_ubs).annotate(
            total=Count('id')
        ).order_by('-total')[:15]

        bairros = []
        if chave == 'dengue':
            from api.utils.importador_dbf import extrair_bairro
            contagem = {}
            for endereco in qs.values_list('endereco', flat=True).iterator():
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

    # Renderiza e gera PDF
    html_string = render_to_string('relatorios/mensal.html', context)
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(html_string.encode("UTF-8")), dest=pdf_buffer)

    if pisa_status.err:
        raise Exception("Erro ao gerar PDF com xhtml2pdf")

    return pdf_buffer.getvalue()