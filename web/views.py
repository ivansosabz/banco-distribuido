from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from accounts.models import Account
from django.shortcuts import redirect
from django.contrib import messages
from .forms import TransferenciaInternaForm
from .forms import TransferenciaExternaForm
from transactions.models import Transaction
from django.db import transaction as db_transaction
import requests

def home(request):
    return render(request, "home.html")


@login_required
def dashboard(request):

    if request.user.is_superuser:
        cuentas = Account.objects.all()
        return render(request, "dashboard_admin.html", {"cuentas": cuentas})

    # Cliente normal
    try:
        cliente = request.user.cliente
        cuentas = cliente.cuentas.all()

        transacciones = []

        for cuenta in cuentas:

            # Transacciones enviadas
            for t in cuenta.transacciones_origen.all():
                transacciones.append(
                    {
                        "tipo": "Enviado",
                        "monto": t.monto,
                        "estado": t.estado,
                    }
                )

            # Transacciones recibidas
            for t in cuenta.transacciones_destino.all():
                transacciones.append(
                    {
                        "tipo": "Recibido",
                        "monto": t.monto,
                        "estado": t.estado,
                    }
                )

    except:
        cuentas = []
        transacciones = []

    return render(
        request,
        "dashboard_cliente.html",
        {"cuentas": cuentas, "transacciones": transacciones},
    )


@login_required
def transferencia_interna(request):

    try:
        cliente = request.user.cliente
        cuentas_cliente = cliente.cuentas.all()
    except:
        cuentas_cliente = []

    if request.method == "POST":
        form = TransferenciaInternaForm(request.POST)
        form.fields["cuenta_origen"].choices = [
            (c.id, c.numero_cuenta) for c in cuentas_cliente
        ]

        if form.is_valid():
            cuenta_origen = Account.objects.get(id=form.cleaned_data["cuenta_origen"])
            numero_destino = form.cleaned_data["numero_cuenta_destino"]
            monto = form.cleaned_data["monto"]

            try:
                cuenta_destino = Account.objects.get(numero_cuenta=numero_destino)

                if cuenta_origen.saldo_actual < monto:
                    messages.error(request, "Saldo insuficiente")
                    return redirect("transferencia_interna")

                with db_transaction.atomic():
                    cuenta_origen.saldo_actual -= monto
                    cuenta_destino.saldo_actual += monto
                    cuenta_origen.save()
                    cuenta_destino.save()

                    Transaction.objects.create(
                        tipo_transaccion=Transaction.TipoTransaccion.INTERNA,
                        cuenta_origen=cuenta_origen,
                        cuenta_destino=cuenta_destino,
                        monto=monto,
                        moneda=cuenta_origen.moneda,
                        estado=Transaction.EstadoTransaccion.COMPLETADA,
                    )

                messages.success(request, "Transferencia realizada correctamente")
                return redirect("dashboard")

            except Account.DoesNotExist:
                messages.error(request, "Cuenta destino no encontrada")

    else:
        form = TransferenciaInternaForm()
        form.fields["cuenta_origen"].choices = [
            (c.id, c.numero_cuenta) for c in cuentas_cliente
        ]

    return render(request, "transferencia_interna.html", {"form": form})


@login_required
def transferencia_externa(request):

    try:
        cliente = request.user.cliente
        cuentas_cliente = cliente.cuentas.all()
    except:
        cuentas_cliente = []

    if request.method == "POST":
        form = TransferenciaExternaForm(request.POST)
        form.fields["cuenta_origen"].choices = [
            (c.id, c.numero_cuenta) for c in cuentas_cliente
        ]

        if form.is_valid():
            cuenta_origen = Account.objects.get(id=form.cleaned_data["cuenta_origen"])
            numero_destino = form.cleaned_data["numero_cuenta_destino"]
            url_destino = form.cleaned_data["url_banco_destino"]
            monto = form.cleaned_data["monto"]

            if cuenta_origen.saldo_actual < monto:
                messages.error(request, "Saldo insuficiente")
                return redirect("transferencia_externa")

            try:
                response = requests.post(
                    url_destino,
                    json={
                        "banco_origen": "Banco Distribuido",
                        "cuenta_destino": numero_destino,
                        "monto": float(monto),
                    },
                    timeout=5,
                )

                if response.status_code == 200:
                    cuenta_origen.saldo_actual -= monto
                    cuenta_origen.save()

                    Transaction.objects.create(
                        tipo_transaccion=Transaction.TipoTransaccion.EXTERNA,
                        cuenta_origen=cuenta_origen,
                        numero_cuenta_externa=numero_destino,
                        monto=monto,
                        moneda=cuenta_origen.moneda,
                        estado=Transaction.EstadoTransaccion.COMPLETADA,
                    )

                    messages.success(request, "Transferencia externa completada")
                    return redirect("dashboard")
                else:
                    messages.error(request, "Error del banco destino")

            except Exception:
                messages.error(request, "No se pudo conectar al banco destino")

    else:
        form = TransferenciaExternaForm()
        form.fields["cuenta_origen"].choices = [
            (c.id, c.numero_cuenta) for c in cuentas_cliente
        ]

    return render(request, "transferencia_externa.html", {"form": form})
