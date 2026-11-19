from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import CanalComunicacao

# Register your models here.
@admin.register(CanalComunicacao)
class CanalComunicacaoAdmin(ModelAdmin):
    list_display = ("id", "author", "title", "content", "date", "time")
    search_fields = ("id", "title")