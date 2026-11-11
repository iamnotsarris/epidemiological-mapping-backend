# cobertura_vacinal/admin.py
from django.contrib import admin
from api.admin import BaseExportAdmin
from .models import CoberturaVacinal

@admin.register(CoberturaVacinal)
class CoberturaVacinalAdmin(BaseExportAdmin):
    list_display = (
        "ano", "imunobiologico", "cobertura_percentual",
        "meta_otima", "data_atualizacao",
    )
    search_fields = (
        "ano", "imunobiologico", "cobertura_percentual",
        "meta_otima", "data_atualizacao",
    )