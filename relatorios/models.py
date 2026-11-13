from django.db import models
from django.contrib.auth.models import User


class RelatorioMensal(models.Model):
    MESES_CHOICES = (
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    )
    mes = models.IntegerField(choices=MESES_CHOICES, verbose_name="Mês")
    ano = models.IntegerField(verbose_name="Ano")
    arquivo_pdf = models.FileField(upload_to='relatorios_pdf/', null=True, blank=True, verbose_name="Arquivo PDF")
    data_geracao = models.DateTimeField(auto_now_add=True)

    gerado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='relatorios_gerados')

    class Meta:
        verbose_name = "Relatório Mensal (PDF)"
        verbose_name_plural = "Relatórios Mensais (PDF)"
        unique_together = ('mes', 'ano')

    def __str__(self):
        return f"Relatório {self.get_mes_display()}/{self.ano}"