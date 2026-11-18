from django.db import models
from django.contrib.auth.models import User

class CanalComunicacao(models.Model):
    author = models.CharField(max_length=150, null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField(max_length=1000)
    image = models.ImageField(upload_to='comunicados/', null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    def __str__(self):
        return self.title