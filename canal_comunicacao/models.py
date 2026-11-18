from django.db import models
from django.contrib.auth.models import User

class CanalComunicacao(models.Model):
    id = models.TextField(null=False, blank=True)
    author = models.TextField(null=True, blank=True)
    title = models.CharField(max_length=200, null=False, blank=False)
    content = models.TextField(max_length=1000, null=False, blank=False)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    def __str__(self):
        return self.title
