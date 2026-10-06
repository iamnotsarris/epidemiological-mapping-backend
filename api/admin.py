import os
from django.contrib import admin
from dbfread import DBF
import pandas as pd
from .utils.importador_dbf import processar_arquivo_dbf, processar_registros
from .models import PacienteDengue, PacienteTuberculose, PacienteSifilis,UploadDBF, PacienteChagas, PacienteViolenciaDomestica, PacienteHans, PacienteHepatite, PacienteAnimaisPec, PacienteIntoxicacao, PacienteLeish, PacienteAidsAdulto, CoberturaVacinal, PerfilUsuario
from datetime import datetime


@admin.register(PacienteDengue)
class PacienteDengueAdmin(admin.ModelAdmin):
    list_display = ("numero_notificacao", "id_unidade", "nome_paciente", "data_notificacao", "endereco", "data_nascimento",
                    "data_pri_sintoma", "id_agravo", "hospital", "cs_sexo", "classi_fin")
    search_fields = ("endereco", "id_unidade")


@admin.register(PacienteTuberculose)
class PacienteTuberculoseAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific", "ano_notific")
    search_fields = ("id_unidade", "nm_ubs", "nu_notific")

@admin.register(PacienteSifilis)
class PacienteSifilisAdmin(admin.ModelAdmin):
    list_display = ("nu_notific", "id_unidade", "un_saude", "nm_ubs", "mu_residen", "nu_notific", "dt_notific", "ano_notific", "id_agravo", "nm_pacient")
    search_fields = ("nu_notific", "nu_notific", "id_agravo", "id_unidade")

@admin.register(PacienteChagas)
class PacienteChagasAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific", "ano_notific")
    search_fields = ("id_unidade", "nm_ubs", "nu_notific")

@admin.register(PacienteViolenciaDomestica)
class PacienteViolenciaDomesticaAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific", "ano_notific")
    search_fields = ("nu_notific", "id_unidade", "nm_ubs")

@admin.register(PacienteHans)
class PacienteHansAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific", "ano_notific")
    search_fields = ("nu_notific", "id_unidade", "nm_ubs")

@admin.register(PacienteHepatite)
class PacienteHepatiteAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "nm_ubs", "nu_notific", "ano_notific")
    search_fields = ("nu_notific", "id_unidade", "nm_ubs")

@admin.register(PacienteAnimaisPec)
class PacienteAnimaisPecAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "nm_ubs", "hospital", "ano_notific", "nu_notific")
    search_fields = ("id_unidade", "nm_ubs", "hospital", "ano_notific", "nu_notific")

@admin.register(PacienteIntoxicacao)
class PacienteIntoxicacaoAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "ano_notific", "nu_notific" )
    search_fields = ("id_unidade","ano_notific", "nu_notific")

@admin.register(PacienteLeish)
class PacienteLeishAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "ano_notific", "nu_notific")
    search_fields = ("id_unidade", "ano_notific", "nu_notific")

@admin.register(PacienteAidsAdulto)
class PacienteAidsAdultoAdmin(admin.ModelAdmin):
    list_display = ("id_unidade", "ano_notific", "nu_notific")
    search_fields = ("id_unidade", "ano_notific", "nu_notific")

@admin.register(CoberturaVacinal)
class CoberturaVacinalAdmin(admin.ModelAdmin):
    list_display = ("ano", 'imunobiologico', "cobertura_percentual", "meta_otima", 'data_atualizacao')
    search_fields = ("ano", 'imunobiologico', "cobertura_percentual", "meta_otima", 'data_atualizacao')

@admin.register(UploadDBF)
class UploadDBFAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        nome_arquivo = os.path.basename(obj.arquivo.name).lower()
        caminho_arquivo = obj.arquivo.path

        # --------- CSV (cobertura vacinal) ---------
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

        # --------- DBF / XLSX (SINAN) ---------
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