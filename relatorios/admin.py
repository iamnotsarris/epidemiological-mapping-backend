from django.contrib import admin
from django.core.files.base import ContentFile
from .models import RelatorioMensal
from api.utils.gerador_pdf import gerar_relatorio_mensal

@admin.register(RelatorioMensal)
class RelatorioMensalAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'data_geracao', 'arquivo_pdf', 'gerado_por')
    readonly_fields = ('arquivo_pdf', 'data_geracao', 'gerado_por')

    def save_model(self, request, obj, form, change):
        if not obj.gerado_por:
            obj.gerado_por = request.user

        super().save_model(request, obj, form, change)

        if not obj.arquivo_pdf:
            nome_arquivo = f"relatorio_{obj.mes:02d}_{obj.ano}.pdf"
            try:
                pdf_bytes = gerar_relatorio_mensal(obj.mes, obj.ano)
                obj.arquivo_pdf.save(nome_arquivo, ContentFile(pdf_bytes), save=True)
                self.message_user(request, f"Relatório {obj} gerado com sucesso!")
            except Exception as e:
                self.message_user(request, f"Erro ao gerar PDF: {e}", level='ERROR')