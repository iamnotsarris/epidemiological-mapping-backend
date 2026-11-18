from django.contrib import admin
from .models import CanalComunicacao

# Register your models here.
@admin.register(CanalComunicacao)
class CanalComunicacaoAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "title", "content", "date", "time")
    search_fields = ("id", "title")