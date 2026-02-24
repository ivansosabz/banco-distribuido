# banks/models.py
from django.db import models


class Bank(models.Model):
    nombre = models.CharField(max_length=100)
    url_api = models.URLField(help_text="Ej: http://192.168.100.55:3000/api/receive-transfer/")
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Banco"
        verbose_name_plural = "Bancos"

    def __str__(self):
        return self.nombre