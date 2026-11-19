from django.db import models
from django.contrib.auth.models import User

class PacienteDengue(models.Model):
    numero_notificacao = models.CharField(max_length=50, null=True, blank=True)
    id_unidade = models.TextField(null=True, blank=True)
    nome_paciente = models.CharField(max_length=100, null=True, blank=True)
    endereco = models.TextField(null=True, blank=True)
    id_agravo = models.TextField(null=True, blank=True)
    hospital = models.TextField(null=True, blank=True)
    cs_sexo = models.TextField(null=True, blank=True)
    classi_fin = models.TextField(null=True, blank=True)
    data_notificacao = models.DateField(null=True, blank=True)
    data_notificacao_precisao = models.CharField(
        max_length=1,
        choices=[('D', 'Dia'), ('M', 'Mês'), ('Y', 'Ano'), ('N', 'Não informado')],
        default='D',
        null=True, blank=True,
    )

    data_pri_sintoma = models.DateField(null=True, blank=True)
    data_pri_sintoma_precisao = models.CharField(
        max_length=1,
        choices=[('D', 'Dia'), ('M', 'Mês'), ('Y', 'Ano'), ('N', 'Não informado')],
        default='D',
        null=True, blank=True,
    )

    data_nascimento = models.DateField(null=True, blank=True)
    data_nascimento_precisao = models.CharField(
        max_length=1,
        choices=[('D', 'Dia'), ('M', 'Mês'), ('Y', 'Ano'), ('N', 'Não informado')],
        default='D',
        null=True, blank=True,
    )

    def __str__(self):
        return f"{self.numero_notificacao} - {self.nome_paciente}"

    class Meta:
        verbose_name = "Dengue"
        verbose_name_plural = "Casos de Dengue"

class PacienteTuberculose(models.Model):
    id_unidade = models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)
    nu_notific = models.TextField(null=True, blank=True)
    ano_notific = models.TextField(null=True, blank=True)


    def __str__(self):
        return f"{self.nm_ubs} - {self.nu_notific}"

    class Meta:
        verbose_name = "Tuberculose"
        verbose_name_plural = "Casos de Tuberculos"

class PacienteSifilis(models.Model):
    nu_notific=models.TextField(null=True, blank=True)
    id_unidade = models.TextField(null=True, blank=True)
    un_saude=models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)
    mu_residen=models.TextField(null=True, blank=True)
    id_agravo=models.TextField(null=True, blank=True)
    nm_pacient=models.TextField(null=True, blank=True)
    ano_notific = models.TextField(null=True, blank=True)

    data_notificacao = models.DateField(null=True, blank=True)
    data_notificacao_precisao = models.CharField(
        max_length=1,
        choices=[('D', 'Dia'), ('M', 'Mês'), ('Y', 'Ano'), ('N', 'Não informado')],
        default='D',
        null=True, blank=True,
    )

    class Meta:
        verbose_name = "Sifilis"
        verbose_name_plural = "Casos de Sifilis"

class PacienteChagas(models.Model):
    id_unidade = models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)
    nu_notific = models.TextField(null=True, blank=True)
    ano_notific = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Chagas"
        verbose_name_plural = "Casos de Chagas"

class PacienteHans(models.Model):
    id_unidade = models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)
    nu_notific = models.TextField(null=True, blank=True)
    ano_notific = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Hanseníase"
        verbose_name_plural = "Casos de Hanseníase"

class PacienteViolenciaDomestica(models.Model):
    nu_notific = models.TextField(null=True, blank=True)
    id_unidade = models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)
    ano_notific = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Violência"
        verbose_name_plural = "Casos de Violência"

class PacienteHepatite(models.Model):
    nu_notific = models.TextField(null=True, blank=True)
    id_unidade = models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)
    hospital = models.TextField(null=True, blank=True)
    ano_notific = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Hepatite"
        verbose_name_plural = "Casos de Hepatites"

class PacienteAnimaisPec(models.Model):
    id_unidade = models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)
    hospital = models.TextField(null=True, blank=True)
    ano_notific = models.TextField(null=True, blank=True)
    nu_notific = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Animail Peçonhento"
        verbose_name_plural = "Casos de Animais Peçonhentos"

class PacienteIntoxicacao(models.Model):
    id_unidade = models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)
    hospital = models.TextField(null=True, blank=True)
    ano_notific = models.TextField(null=True, blank=True)
    nu_notific = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Intoxicação"
        verbose_name_plural = "Casos de Intoxicações"

class PacienteLeish(models.Model):
    id_unidade = models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)
    hospital = models.TextField(null=True, blank=True)
    ano_notific = models.TextField(null=True, blank=True)
    nu_notific = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Leishmoníase"
        verbose_name_plural = "Casos de Leishmoníase"

class PacienteAidsAdulto(models.Model):
    id_unidade = models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)
    hospital = models.TextField(null=True, blank=True)
    ano_notific = models.TextField(null=True, blank=True)
    nu_notific = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Aids Adulto"
        verbose_name_plural = "Casos de Aids Adultos"

class UploadDBF(models.Model):
    arquivo = models.FileField(upload_to='dbfs/')
    data_upload = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.arquivo}"


class PerfilUsuario(models.Model):
    TIPO_USUARIO = (
        ('ADMIN', 'Administrador'),
        ('UBS', 'Unidade Básica de Saúde'),
    )
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    role = models.CharField(max_length=10, choices=TIPO_USUARIO, default='UBS')
    id_unidade = models.CharField(max_length=50, null=True, blank=True, help_text="Preencha com o ID da Unidade (CNES) se for UBS")

    def __str__(self):
        return f"{self.usuario.username} - {self.role}"