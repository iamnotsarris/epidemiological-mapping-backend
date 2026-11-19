# cobertura_vacinal/admin.py
from django.contrib import admin
from api.admin import BaseExportAdmin
from .models import CoberturaVacinal

@admin.register(CoberturaVacinal)
class CoberturaVacinalAdmin(BaseExportAdmin):
    list_filter = ("ano", "imunobiologico")
    list_filter_submit = True
    ordering = ("-ano", "imunobiologico")
    search_fields = ("imunobiologico",)