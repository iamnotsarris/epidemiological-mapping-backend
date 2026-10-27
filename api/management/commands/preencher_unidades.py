from django.core.management.base import BaseCommand
from api.models import PacienteDengue
from api.utils.importador_dbf import (
    extrair_bairro,
    BAIRRO_PARA_UBS_NOME,
    UBS_NOME_PARA_CNES,
    UNIDADE_NOTIFICADORA_PARA_UBS  # <-- Importante trazer esse dicionário
)


class Command(BaseCommand):
    help = "Traduz códigos de hospitais para UBS e preenche id_unidade vazio com base no bairro"

    def handle(self, *args, **kwargs):
        traduzidos = 0
        preenchidos = 0

        # Usando .iterator() para não estourar a memória se a base for muito grande
        # Se a base for pequena (ex: menos de 50 mil linhas), pode deixar só .all()
        pacientes = PacienteDengue.objects.all().iterator()

        for p in pacientes:
            alterou = False

            # 1. Traduzir códigos que são de hospitais/CAPS para a UBS correspondente
            if p.id_unidade and str(p.id_unidade) in UNIDADE_NOTIFICADORA_PARA_UBS:
                novo_id = UNIDADE_NOTIFICADORA_PARA_UBS[str(p.id_unidade)]
                # Verifica se realmente houve mudança (pra não salvar à toa)
                if str(p.id_unidade) != str(novo_id):
                    p.id_unidade = novo_id
                    alterou = True
                    traduzidos += 1

            # 2. Preencher id_unidade que continuam vazios (ou que não foram traduzidos) com base no bairro
            if not p.id_unidade:
                bairro = extrair_bairro(p.endereco)
                if bairro:
                    nome_ubs = BAIRRO_PARA_UBS_NOME.get(bairro)
                    if nome_ubs:
                        cnes = UBS_NOME_PARA_CNES.get(nome_ubs)
                        if cnes:
                            p.id_unidade = cnes
                            alterou = True
                            preenchidos += 1

            # 3. Salva apenas se alguma das regras acima alterou o dado
            if alterou:
                p.save(update_fields=['id_unidade'])

        self.stdout.write(self.style.SUCCESS(
            f"Tradução concluída! "
            f"{traduzidos} códigos de hospitais/notificadores foram traduzidos para UBS. "
            f"{preenchidos} registros nulos foram preenchidos com base no bairro."
        ))