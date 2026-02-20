from django.contrib import admin
from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "numero_cuenta",
        "cliente",
        "tipo_cuenta",
        "saldo_actual",
        "moneda",
        "estado",
    )

    list_filter = ("tipo_cuenta", "estado", "moneda")
    search_fields = ("numero_cuenta", "cliente__nombres")
