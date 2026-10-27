import os
from django.contrib import admin, messages
from django.http import HttpResponse
from dbfread import DBF
import pandas as pd
from .utils.importador_dbf import processar_arquivo_dbf, processar_registros
from .utils.exportador import exportar
from .models import (
    PacienteDengue, PacienteTuberculose, PacienteSifilis, UploadDBF,
    PacienteChagas, PacienteViolenciaDomestica, PacienteHans,
    PacienteHepatite, PacienteAnimaisPec, PacienteIntoxicacao,
    PacienteLeish, PacienteAidsAdulto, CoberturaVacinal, PerfilUsuario,
)
from datetime import datetime


class BaseExportAdmin(admin.ModelAdmin):
    """Adiciona 3 ações de exportação (CSV, XLSX, DBF) a qualquer ModelAdmin."""
    actions = ["acao_exportar_csv", "acao_exportar_xlsx", "acao_exportar_dbf"]

    def _exportar_queryset(self, request, queryset, formato):
        modelo = self.model
        try:
            conteudo, mimetype, ext = exportar(queryset, modelo, formato)
        except ImportError as e:
            self.message_user(request, str(e), level=messages.ERROR)
            return None
        except Exception as e:
            self.message_user(
                request, f"Erro ao exportar {formato.upper()}: {e}",
                level=messages.ERROR,
            )
            return None

        nome_base = modelo._meta.model_name
        response = HttpResponse(conteudo, content_type=mimetype)
        response["Content-Disposition"] = (
            f'attachment; filename="{nome_base}.{ext}"'
        )
        return response

    @admin.action(description="Exportar selecionados como CSV")
    def acao_exportar_csv(self, request, queryset):
        return self._exportar_queryset(request, queryset, "csv")

    @admin.action(description="Exportar selecionados como XLSX (Excel)")
    def acao_exportar_xlsx(self, request, queryset):
        return self._exportar_queryset(request, queryset, "xlsx")

    @admin.action(description="Exportar selecionados como DBF")
    def acao_exportar_dbf(self, request, queryset):
        return self._exportar_queryset(request, queryset, "dbf")

@admin.register(PacienteDengue)
class PacienteDengueAdmin(BaseExportAdmin):
    list_display = (
        "numero_notificacao", "id_unidade", "nome_paciente",
        "data_notificacao", "data_notificacao_precisao",
        "data_nascimento", "data_nascimento_precisao",
        "data_pri_sintoma", "data_pri_sintoma_precisao",
        "id_agravo", "hospital", "cs_sexo", "classi_fin",
    )
    list_filter = ("data_notificacao_precisao", "data_nascimento_precisao",
                   "data_pri_sintoma_precisao")


@admin.register(PacienteTuberculose)
class PacienteTuberculoseAdmin(BaseExportAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific", "ano_notific")
    search_fields = ("id_unidade", "nm_ubs", "nu_notific")


@admin.register(PacienteSifilis)
class PacienteSifilisAdmin(BaseExportAdmin):
    list_display = (
        "nu_notific", "id_unidade", "un_saude", "nm_ubs", "mu_residen",
        "data_notificacao", "data_notificacao_precisao",
        "ano_notific", "id_agravo", "nm_pacient",
    )
    list_filter = ("data_notificacao_precisao",)
    search_fields = ("nu_notific", "id_agravo", "id_unidade")


@admin.register(PacienteChagas)
class PacienteChagasAdmin(BaseExportAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific", "ano_notific")
    search_fields = ("id_unidade", "nm_ubs", "nu_notific")


@admin.register(PacienteViolenciaDomestica)
class PacienteViolenciaDomesticaAdmin(BaseExportAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific", "ano_notific")
    search_fields = ("nu_notific", "id_unidade", "nm_ubs")


@admin.register(PacienteHans)
class PacienteHansAdmin(BaseExportAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific", "ano_notific")
    search_fields = ("nu_notific", "id_unidade", "nm_ubs")


@admin.register(PacienteHepatite)
class PacienteHepatiteAdmin(BaseExportAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific", "ano_notific")
    search_fields = ("nu_notific", "id_unidade", "nm_ubs")


@admin.register(PacienteAnimaisPec)
class PacienteAnimaisPecAdmin(BaseExportAdmin):
    list_display = ("id_unidade", "nm_ubs", "hospital", "ano_notific", "nu_notific")
    search_fields = ("id_unidade", "nm_ubs", "hospital", "ano_notific", "nu_notific")


@admin.register(PacienteIntoxicacao)
class PacienteIntoxicacaoAdmin(BaseExportAdmin):
    list_display = ("id_unidade", "nm_ubs", "hospital", "ano_notific", "nu_notific")
    search_fields = ("id_unidade", "nm_ubs", "hospital", "ano_notific", "nu_notific")


@admin.register(PacienteLeish)
class PacienteLeishAdmin(BaseExportAdmin):
    list_display = ("id_unidade", "nm_ubs", "hospital", "ano_notific", "nu_notific")
    search_fields = ("id_unidade", "nm_ubs", "hospital", "ano_notific", "nu_notific")


@admin.register(PacienteAidsAdulto)
class PacienteAidsAdultoAdmin(BaseExportAdmin):
    list_display = ("id_unidade", "nm_ubs", "hospital", "ano_notific", "nu_notific")
    search_fields = ("id_unidade", "nm_ubs", "hospital", "ano_notific", "nu_notific")


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


@admin.register(UploadDBF)
class UploadDBFAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        nome_arquivo = os.path.basename(obj.arquivo.name).lower()
        caminho_arquivo = obj.arquivo.path

        if nome_arquivo.endswith('.csv'):
            try:
                df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8', low_memory=False)
                df.columns = df.columns.str.lower()

                coluna_municipio = 'municipio' if 'municipio' in df.columns else 'no_municipio'
                if coluna_municipio in df.columns:
                    df = df[df[coluna_municipio].str.upper() == 'FLORIANO']

                if 'doses_aplicadas' in df.columns and 'populacao_alvo' in df.columns:
                    df['doses_aplicadas'] = pd.to_numeric(df['doses_aplicadas'], errors='coerce').fillna(0)
                    df['populacao_alvo'] = pd.to_numeric(df['populacao_alvo'], errors='coerce').fillna(0)
                    df_agrupado = df.groupby(['ano', 'imunobiologico']).sum().reset_index()
                    df_agrupado['cobertura'] = (
                        df_agrupado['doses_aplicadas'] / df_agrupado['populacao_alvo']
                    ) * 100
                    df_agrupado['cobertura'] = df_agrupado['cobertura'].fillna(0)

                    for _, row in df_agrupado.iterrows():
                        meta = 90.0 if 'rotav' in str(row['imunobiologico']).lower() else 95.0
                        CoberturaVacinal.objects.update_or_create(
                            ano=int(row['ano']),
                            imunobiologico=str(row['imunobiologico']).strip(),
                            defaults={
                                'cobertura_percentual': round(row['cobertura'], 2),
                                'meta_otima': meta,
                            }
                        )
            except Exception as e:
                print(f"Erro ao processar CSV de Vacinas: {e}")
            return

        try:
            if nome_arquivo.endswith('.dbf'):
                resultado = processar_arquivo_dbf(caminho_arquivo, nome_original=nome_arquivo)
            elif nome_arquivo.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(caminho_arquivo)
                df.columns = [str(c).strip().upper() for c in df.columns]
                df = df.where(pd.notnull(df), None)
                resultado = processar_registros(df.to_dict(orient='records'), nome_arquivo)
            else:
                return
            print(f"[Upload] {nome_arquivo}: {resultado}")
        except Exception as e:
            print(f"Erro ao processar arquivo: {e}")


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'role', 'id_unidade')
    list_filter = ('role',)
    search_fields = ('usuario__username', 'id_unidade')
    help_text = "Para UBS, o 'id_unidade' deve ser o CNES exato que vem no DBF."