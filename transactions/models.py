import uuid
from django.db import models, transaction as db_transaction
from django.utils import timezone
from accounts.models import Account
import requests


class Transaction(models.Model):

    class TipoTransaccion(models.TextChoices):
        INTERNA = "interna", "Transferencia Interna"
        EXTERNA = "externa", "Transferencia Externa"

    class EstadoTransaccion(models.TextChoices):
        COMPLETADA = "completada", "Completada"
        PENDIENTE = "pendiente", "Pendiente"
        RECHAZADA = "rechazada", "Rechazada"
        REVERSADA = "reversada", "Reversada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tipo_transaccion = models.CharField(max_length=20, choices=TipoTransaccion.choices)

    cuenta_origen = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="transacciones_origen"
    )

    cuenta_destino = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transacciones_destino",
    )

    numero_cuenta_externa = models.CharField(
        max_length=20, 
        null=True, 
        blank=True
    )

    monto = models.DecimalField(max_digits=15, decimal_places=2)

    moneda = models.CharField(max_length=5, choices=Account.Moneda.choices)

    fecha = models.DateTimeField(default=timezone.now)

    estado = models.CharField(
        max_length=20,
        choices=EstadoTransaccion.choices,
        default=EstadoTransaccion.PENDIENTE,
    )

    def __str__(self):
        return f"{self.tipo_transaccion} - {self.monto} {self.moneda}"

    def procesar_transferencia_interna(self):
        if self.tipo_transaccion != self.TipoTransaccion.INTERNA:
            raise ValueError("No es una transferencia interna")

        if self.monto <= 0:
            self.estado = self.EstadoTransaccion.RECHAZADA
            self.save()
            return "Monto inválido"

        if self.cuenta_origen.saldo_actual < self.monto:
            self.estado = self.EstadoTransaccion.RECHAZADA
            self.save()
            return "Saldo insuficiente"

        with db_transaction.atomic():  # significa que se hará todo o nada, si algo falla, se revierte todo
            self.cuenta_origen.saldo_actual -= self.monto
            self.cuenta_destino.saldo_actual += self.monto

            self.cuenta_origen.save()
            self.cuenta_destino.save()

            self.estado = self.EstadoTransaccion.COMPLETADA
            self.save()

        return "Transferencia interna completada"

    def procesar_transferencia_externa(self, url_destino):

        if self.tipo_transaccion != self.TipoTransaccion.EXTERNA:
            raise ValueError("No es una transferencia externa")

        if self.monto <= 0:
            self.estado = self.EstadoTransaccion.RECHAZADA
            self.save()
            return "Monto inválido"

        if self.cuenta_origen.saldo_actual < self.monto:
            self.estado = self.EstadoTransaccion.RECHAZADA
            self.save()
            return "Saldo insuficiente"

        try:
            # Descontar saldo
            self.cuenta_origen.saldo_actual -= self.monto
            self.cuenta_origen.save()

            response = requests.post(
                url_destino,
                json={
                    "banco_origen": "Banco Distribuido",
                    "cuenta_destino": self.numero_cuenta_externa,
                    "monto": float(self.monto),
                },
                timeout=5,
            )
            print(response.status_code)
            print(response.text)

            if response.status_code == 200:
                self.estado = self.EstadoTransaccion.COMPLETADA
                self.save()
                return "Transferencia externa completada"

            else:
                # Revertir
                self.cuenta_origen.saldo_actual += self.monto
                self.cuenta_origen.save()

                self.estado = self.EstadoTransaccion.RECHAZADA
                self.save()

                return "Error en banco destino"

        except Exception as e:
            # Revertir
            self.cuenta_origen.saldo_actual += self.monto
            self.cuenta_origen.save()

            self.estado = self.EstadoTransaccion.RECHAZADA
            self.save()

            return f"Error de conexión: {str(e)}"
