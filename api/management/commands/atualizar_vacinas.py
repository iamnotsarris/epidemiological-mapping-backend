from django.core.management.base import BaseCommand
from api.models import CoberturaVacinal


class Command(BaseCommand):
    help = 'Popula o banco com dados de cobertura vacinal para o dashboard'

    def handle(self, *args, **options):
        # Dados extraídos do seu painel do Qlik Sense para 2026
        vacinas = [
            {'imunobiologico': 'BCG', 'cobertura': 93.93, 'meta': 95.0},
            {'imunobiologico': 'Poliomielite', 'cobertura': 87.54, 'meta': 95.0},
            {'imunobiologico': 'Pneumocócica Conjugada', 'cobertura': 90.08, 'meta': 95.0},
            {'imunobiologico': 'Meningocócica Conjugada', 'cobertura': 88.93, 'meta': 95.0},
            {'imunobiologico': 'Penta (DTP/HepB/Hib)', 'cobertura': 87.04, 'meta': 95.0},
            {'imunobiologico': 'Rotavírus', 'cobertura': 88.24, 'meta': 90.0},
        ]

        try:
            for v in vacinas:
                CoberturaVacinal.objects.update_or_create(
                    ano=2026,
                    imunobiologico=v['imunobiologico'],
                    defaults={
                        'cobertura_percentual': v['cobertura'],
                        'meta_otima': v['meta']
                    }
                )

            self.stdout.write(
                self.style.SUCCESS('Dados de vacinação salvos com sucesso! Abra o frontend para verificar.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro no processamento: {e}'))