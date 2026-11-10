# api/utils/gerador_pdf.py
import io
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.db.models import Count
from api.models import PacienteDengue, PacienteSifilis, PacienteTuberculose, CoberturaVacinal
from api.utils.assistente import DOENCAS, _normalizar_doenca


def gerar_relatorio_mensal(mes, ano, agravo='geral'):  # ✅ Alterado para agravo
    MESES_NOMES = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro",
                   "Outubro", "Novembro", "Dezembro"]

    context = {
        "mes": mes, "mes_nome": MESES_NOMES[mes], "ano": ano, "agravo": agravo  # ✅ Enviando 'agravo' para o HTML
    }

    if agravo == 'geral':
        # --- LÓGICA DO PANORAMA GERAL ---
        kpis = {
            "dengue": PacienteDengue.objects.filter(data_notificacao__month=mes, data_notificacao__year=ano).count(),
            "sifilis": PacienteSifilis.objects.filter(data_notificacao__month=mes, data_notificacao__year=ano).count(),
            "tuberculose": PacienteTuberculose.objects.filter(ano_notific=str(ano)).count(),
        }
        vacinas = CoberturaVacinal.objects.filter(ano=ano).order_by('imunobiologico')

        agravos_ubs = PacienteDengue.objects.filter(
            data_notificacao__month=mes, data_notificacao__year=ano
        ).values('id_unidade').annotate(dengue_count=Count('id')).order_by('-dengue_count')[:10]

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
        if 'data_notificacao' in campo_ano:
            qs = qs.filter(data_notificacao__month=mes, data_notificacao__year=ano)
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
            "agravo_nome": chave.capitalize(),  # ✅ Alterado para agravo_nome
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