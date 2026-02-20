import uuid
from django.db import models
from django.utils import timezone
from clients.models import Client


class Account(models.Model):

    class TipoCuenta(models.TextChoices):
        CAJA_AHORRO = "caja_ahorro", "Caja de Ahorro"
        CUENTA_CORRIENTE = "cuenta_corriente", "Cuenta Corriente"
        PLAZO_FIJO = "plazo_fijo", "Plazo Fijo"

    class Moneda(models.TextChoices):
        PYG = "PYG", "Guaraníes"
        USD = "USD", "Dólares"

    class EstadoCuenta(models.TextChoices):
        ACTIVA = "activa", "Activa"
        INACTIVA = "inactiva", "Inactiva"
        BLOQUEADA = "bloqueada", "Bloqueada"
        CERRADA = "cerrada", "Cerrada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    cliente = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="cuentas"
    )

    numero_cuenta = models.CharField(max_length=20, unique=True)

    tipo_cuenta = models.CharField(max_length=30, choices=TipoCuenta.choices)

    saldo_actual = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    moneda = models.CharField(max_length=5, choices=Moneda.choices, default=Moneda.PYG)

    fecha_apertura = models.DateTimeField(default=timezone.now)

    estado = models.CharField(
        max_length=20, choices=EstadoCuenta.choices, default=EstadoCuenta.ACTIVA
    )

    limite_transferencia_diaria = models.DecimalField(
        max_digits=15, decimal_places=2, default=10000000
    )

    def __str__(self):
        return f"{self.numero_cuenta} - {self.cliente.nombres}"
