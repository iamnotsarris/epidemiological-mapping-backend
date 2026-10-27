from django.core.management.base import BaseCommand
from api.models import CoberturaVacinal


class Command(BaseCommand):
    help = 'Popula o banco com dados de cobertura vacinal para o dashboard'

    def handle(self, *args, **options):
        ano_alvo = 2026

        # Limpa os dados do ano para evitar duplicatas antes de inserir os novos
        CoberturaVacinal.objects.filter(ano=ano_alvo).delete()
        self.stdout.write(self.style.WARNING(f'Dados antigos de {ano_alvo} limpos.'))

        vacinas = [
            # Ao Nascer (Dados do site do Gov)
            {'imunobiologico': 'BCG', 'cobertura': 94.52, 'meta': 90.0},
            {'imunobiologico': 'Hepatite B (<= 30 dias)', 'cobertura': 96.79, 'meta': 95.0},

            # Menores de 1 ano (Dados do site do Gov)
            {'imunobiologico': 'Febre Amarela', 'cobertura': 77.81, 'meta': 95.0},
            {'imunobiologico': 'Poliomielite', 'cobertura': 88.22, 'meta': 95.0},
            {'imunobiologico': 'Pneumocócica Conjugada', 'cobertura': 91.49, 'meta': 95.0},
            {'imunobiologico': 'Meningocócica Conjugada', 'cobertura': 89.55, 'meta': 95.0},
            {'imunobiologico': 'Penta (DTP/HepB/Hib)', 'cobertura': 87.72, 'meta': 95.0},
            {'imunobiologico': 'Rotavírus', 'cobertura': 89.69, 'meta': 90.0},

            # 1 ano de idade (Dados do site do Gov)
            {'imunobiologico': 'Hepatite A Infantil', 'cobertura': 83.04, 'meta': 95.0},
            {'imunobiologico': 'DTP (1º Reforço)', 'cobertura': 83.90, 'meta': 95.0},
            {'imunobiologico': 'Tríplice Viral - 1º Dose', 'cobertura': 94.67, 'meta': 95.0},
            {'imunobiologico': 'Tríplice Viral - 2º Dose', 'cobertura': 79.78, 'meta': 95.0},
            {'imunobiologico': 'Pneumocócica Conjugada (1º Reforço)', 'cobertura': 90.28, 'meta': 95.0},
            {'imunobiologico': 'Poliomielite (1º Reforço)', 'cobertura': 84.12, 'meta': 95.0},
            {'imunobiologico': 'Varicela', 'cobertura': 80.92, 'meta': 95.0},
            {'imunobiologico': 'Meningocócica Conjugada (1º Reforço)', 'cobertura': 92.98, 'meta': 95.0},

            # 4 anos de idade (Como não tem print do Gov para 4 anos, usei os dados do seu Admin, que estão mais atualizados)
            {'imunobiologico': 'DTP (2º Reforço)', 'cobertura': 81.59, 'meta': 95.0},
            {'imunobiologico': 'Varicela - 2º dose', 'cobertura': 78.93, 'meta': 95.0},
            {'imunobiologico': 'Febre Amarela (Reforço)', 'cobertura': 77.81, 'meta': 95.0},
            # Usei o valor de 15/Out que parece ser o mais recente
        ]

        try:
            for v in vacinas:
                CoberturaVacinal.objects.create(
                    ano=ano_alvo,
                    imunobiologico=v['imunobiologico'],
                    cobertura_percentual=v['cobertura'],
                    meta_otima=v['meta']
                )

            self.stdout.write(
                self.style.SUCCESS('Dados de vacinação atualizados e salvos com sucesso!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro no processamento: {e}'))