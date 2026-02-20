from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "tipo_transaccion",
        "cuenta_origen",
        "cuenta_destino",
        "monto",
        "moneda",
        "estado",
        "fecha",
    )

    list_filter = ("tipo_transaccion", "estado")
    search_fields = ("cuenta_origen__numero_cuenta",)
