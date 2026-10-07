from django.core.management.base import BaseCommand
from api.models import PacienteDengue
from api.utils.importador_dbf import (
    extrair_bairro, BAIRRO_PARA_UBS_NOME, UBS_NOME_PARA_CNES
)


class Command(BaseCommand):
    help = "Preenche id_unidade vazio nos pacientes com base no bairro"

    def handle(self, *args, **kwargs):
        atualizados = 0
        for p in PacienteDengue.objects.filter(id_unidade__isnull=True):
            bairro = extrair_bairro(p.endereco)
            nome_ubs = BAIRRO_PARA_UBS_NOME.get(bairro)
            if nome_ubs:
                p.id_unidade = UBS_NOME_PARA_CNES.get(nome_ubs)
                p.save(update_fields=['id_unidade'])
                atualizados += 1
        self.stdout.write(self.style.SUCCESS(f"{atualizados} pacientes atualizados"))