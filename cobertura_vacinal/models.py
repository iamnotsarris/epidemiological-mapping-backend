# cobertura_vacinal/models.py
from django.db import models

class CoberturaVacinal(models.Model):
    ano = models.IntegerField()
    imunobiologico = models.CharField(max_length=100)
    cobertura_percentual = models.FloatField()
    meta_otima = models.FloatField(default=95.0)
    data_atualizacao = models.DateField(auto_now=True)

    class Meta:
        verbose_name = "Cobertura Vacinal"
        verbose_name_plural = "Coberturas Vacinais"
        unique_together = ('ano', 'imunobiologico')

    def __str__(self):
        return f"{self.imunobiologico} ({self.ano}) - {self.cobertura_percentual}%"