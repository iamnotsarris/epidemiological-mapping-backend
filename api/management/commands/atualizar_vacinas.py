from django.core.management.base import BaseCommand
from api.models import CoberturaVacinal


class Command(BaseCommand):
    help = 'Popula o banco com dados de cobertura vacinal para o dashboard'

    def handle(self, *args, **options):
        vacinas = [
            # Ao Nascer
            {'imunobiologico': 'BCG', 'cobertura': 93.93, 'meta': 95.0},
            {'imunobiologico': 'Hepatite B (<= 30 dias)', 'cobertura': 96.31, 'meta': 95.0},

            # Menores de 1 ano
            {'imunobiologico': 'Febre Amarela', 'cobertura': 77.59, 'meta': 95.0},
            {'imunobiologico': 'Poliomielite', 'cobertura': 87.54, 'meta': 95.0},
            {'imunobiologico': 'Pneumocócica Conjugada', 'cobertura': 90.08, 'meta': 95.0},
            {'imunobiologico': 'Meningocócica Conjugada', 'cobertura': 88.93, 'meta': 95.0},
            {'imunobiologico': 'Penta (DTP/HepB/Hib)', 'cobertura': 87.04, 'meta': 95.0},
            {'imunobiologico': 'Rotavírus', 'cobertura': 88.24, 'meta': 90.0},

            # 1 ano de idade
            {'imunobiologico': 'Hepatite A Infantil', 'cobertura': 80.77, 'meta': 95.0},
            {'imunobiologico': 'DTP (1º Reforço)', 'cobertura': 81.37, 'meta': 95.0},
            {'imunobiologico': 'Tríplice Viral - 1º Dose', 'cobertura': 92.71, 'meta': 95.0},
            {'imunobiologico': 'Tríplice Viral - 2º Dose', 'cobertura': 77.10, 'meta': 95.0},
            {'imunobiologico': 'Pneumocócica Conjugada (1º Reforço)', 'cobertura': 88.64, 'meta': 95.0},
            {'imunobiologico': 'Poliomielite (1º Reforço)', 'cobertura': 81.76, 'meta': 95.0},
            {'imunobiologico': 'Varicela', 'cobertura': 78.84, 'meta': 95.0},
            {'imunobiologico': 'Meningocócica Conjugada (1º Reforço)', 'cobertura': 91.45, 'meta': 95.0},

            # 4 anos de idade
            {'imunobiologico': 'DTP (2º Reforço)', 'cobertura': 79.91, 'meta': 95.0},
            {'imunobiologico': 'Varicela - 2º dose', 'cobertura': 77.56, 'meta': 95.0},
            {'imunobiologico': 'Febre Amarela (Reforço)', 'cobertura': 74.69, 'meta': 95.0},
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