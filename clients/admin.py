from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "nombres",
        "apellidos",
        "numero_identificacion",
        "tipo_identificacion",
        "estado",
        "fecha_creacion",
    )

    list_filter = ("estado", "tipo_identificacion")
    search_fields = ("nombres", "apellidos", "numero_identificacion")
