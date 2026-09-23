from django.db import models

# Classe do Paciente
class PacienteDengue(models.Model):
    numero_notificacao = models.CharField(max_length=50, null=True, blank=True)
    id_unidade = models.TextField(null=True, blank=True)
    nome_paciente = models.CharField(max_length=100, null=True, blank=True)
    endereco = models.TextField(null=True, blank=True)
    data_notificacao = models.DateField(null=True, blank=True)
    data_pri_sintoma = models.DateField(null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    id_agravo = models.TextField(null=True, blank=True)
    hospital = models.TextField(null=True, blank=True)
    cs_sexo = models.TextField(null=True, blank=True)
    classi_fin = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.numero_notificacao} - {self.nome_paciente}"

class PacienteTuberculose(models.Model):
    id_unidade = models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)
    nu_notific = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.nm_ubs} - {self.nu_notific}"

class PacienteSifilis(models.Model):
    nu_notific=models.TextField(null=True, blank=True)
    id_unidade = models.TextField(null=True, blank=True)
    un_saude=models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)
    mu_residen=models.TextField(null=True, blank=True)
    dt_notific=models.DateField(null=True, blank=True)
    id_agravo=models.TextField(null=True, blank=True)
    nm_pacient=models.TextField(null=True, blank=True)

class PacienteChagas(models.Model):
    id_unidade = models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)
    nu_notific = models.TextField(null=True, blank=True)

class PacienteHans(models.Model):
    id_unidade = models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)
    nu_notific = models.TextField(null=True, blank=True)

class PacienteViolenciaDomestica(models.Model):
    nu_notific = models.TextField(null=True, blank=True)
    id_unidade = models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)

class PacienteHepatite(models.Model):
    nu_notific = models.TextField(null=True, blank=True)
    id_unidade = models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)

class PacienteAnimaisPec(models.Model):
    id_unidade = models.TextField(null=True, blank=True)
    nm_ubs = models.TextField(null=True, blank=True)
    hospital = models.TextField(null=True, blank=True)
    ano_notific = models.TextField(null=True, blank=True)
    nu_notific = models.TextField(null=True, blank=True)

class PacienteIntoxicacao(models.Model):
    ano_notific = models.TextField(null=True, blank=True)
    nu_notific = models.TextField(null=True, blank=True)

class PacienteLeish(models.Model):
    ano_notific = models.TextField(null=True, blank=True)
    nu_notific = models.TextField(null=True, blank=True)

class PacienteAidsAdulto(models.Model):
    ano_notific = models.TextField(null=True, blank=True)
    nu_notific = models.TextField(null=True, blank=True)

class UploadDBF(models.Model):
    arquivo = models.FileField(upload_to='dbfs/')
    data_upload = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.arquivo}"

class CoberturaVacinal(models.Model):
    ano = models.IntegerField()
    imunobiologico = models.CharField(max_length=100)
    cobertura_percentual = models.FloatField()
    meta_otima = models.FloatField(default=95.0)
    data_atualizacao = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.imunobiologico} ({self.ano}) - {self.cobertura_percentual}%"