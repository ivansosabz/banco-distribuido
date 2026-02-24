from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction as db_transaction
from accounts.models import Account
from transactions.models import Transaction
from .forms import TransferenciaInternaForm, TransferenciaExternaForm
import requests


def _get_choices(cuentas_cliente):
    return [(c.id, c.numero_cuenta) for c in cuentas_cliente]


def home(request):
    return render(request, "home.html")


@login_required
def dashboard(request):

    if request.user.is_superuser:
        cuentas = Account.objects.all()
        return render(request, "dashboard_admin.html", {"cuentas": cuentas})

    # Cliente normal
    cliente = request.user.cliente
    cuentas = cliente.cuentas.all()

    transacciones = []

    for cuenta in cuentas:

        # Enviadas
        for t in cuenta.transacciones_origen.all():
            transacciones.append(
                {
                    "direccion": "Enviado",
                    "tipo": t.tipo_transaccion,
                    "monto": t.monto,
                    "estado": t.estado,
                    "fecha": t.fecha,
                }
            )

        # Recibidas
        for t in cuenta.transacciones_destino.all():
            transacciones.append(
                {
                    "direccion": "Recibido",
                    "tipo": t.tipo_transaccion,
                    "monto": t.monto,
                    "estado": t.estado,
                    "fecha": t.fecha,
                }
            )

    transacciones.sort(key=lambda x: x["fecha"], reverse=True)

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
    except AttributeError:
        cuentas_cliente = []

    choices = _get_choices(cuentas_cliente)

    if request.method == "POST":
        form = TransferenciaInternaForm(request.POST)
        form.fields["cuenta_origen"].choices = choices

        if form.is_valid():
            cuenta_origen = Account.objects.get(id=form.cleaned_data["cuenta_origen"])
            numero_destino = form.cleaned_data["numero_cuenta_destino"]
            monto = form.cleaned_data["monto"]

            try:
                cuenta_destino = Account.objects.get(numero_cuenta=numero_destino)

                # Segunda línea de defensa (el form ya valida esto)
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
        form.fields["cuenta_origen"].choices = choices

    return render(request, "transferencia_interna.html", {"form": form})


# @login_required
# def transferencia_externa(request):
#
#     try:
#         cliente = request.user.cliente
#         cuentas_cliente = cliente.cuentas.all()
#     except AttributeError:
#         cuentas_cliente = []
#
#     choices = _get_choices(cuentas_cliente)
#
#     if request.method == "POST":
#         form = TransferenciaExternaForm(request.POST)
#         form.fields["cuenta_origen"].choices = choices
#
#         if form.is_valid():
#             cuenta_origen = Account.objects.get(id=form.cleaned_data["cuenta_origen"])
#             numero_destino = form.cleaned_data["numero_cuenta_destino"]
#             url_destino = form.cleaned_data["url_banco_destino"]
#             monto = form.cleaned_data["monto"]
#
#             # Segunda línea de defensa (el form ya valida esto)
#             if cuenta_origen.saldo_actual < monto:
#                 messages.error(request, "Saldo insuficiente")
#                 return redirect("transferencia_externa")
#
#             try:
#                 response = requests.post(
#                     url_destino,
#                     json={
#                         "banco_origen": "Banco Distribuido",
#                         "cuenta_destino": numero_destino,
#                         "monto": float(monto),
#                     },
#                     timeout=5,
#                 )
#
#                 if response.status_code == 200:
#                     cuenta_origen.saldo_actual -= monto
#                     cuenta_origen.save()
#
#                     Transaction.objects.create(
#                         tipo_transaccion=Transaction.TipoTransaccion.EXTERNA,
#                         cuenta_origen=cuenta_origen,
#                         numero_cuenta_externa=numero_destino,
#                         monto=monto,
#                         moneda=cuenta_origen.moneda,
#                         estado=Transaction.EstadoTransaccion.COMPLETADA,
#                     )
#
#                     messages.success(request, "Transferencia externa completada")
#                     return redirect("dashboard")
#                 else:
#                     messages.error(request, "Error del banco destino")
#
#             except requests.RequestException:
#                 messages.error(request, "No se pudo conectar al banco destino")
#
#     else:
#         form = TransferenciaExternaForm()
#         form.fields["cuenta_origen"].choices = choices
#
#     return render(request, "transferencia_externa.html", {"form": form})

@login_required
def transferencia_externa(request):

    try:
        cliente = request.user.cliente
        cuentas_cliente = cliente.cuentas.all()
    except AttributeError:
        cuentas_cliente = []

    choices = _get_choices(cuentas_cliente)

    if request.method == "POST":
        form = TransferenciaExternaForm(request.POST)
        form.fields["cuenta_origen"].choices = choices

        if form.is_valid():
            cuenta_origen = Account.objects.get(id=form.cleaned_data["cuenta_origen"])
            numero_destino = form.cleaned_data["numero_cuenta_destino"]
            banco = form.cleaned_data["banco_destino"]  # objeto Bank
            monto = form.cleaned_data["monto"]

            if cuenta_origen.saldo_actual < monto:
                messages.error(request, "Saldo insuficiente")
                return redirect("transferencia_externa")

            try:
                response = requests.post(
                    banco.url_api,  # ← la URL viene del objeto Bank
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
                        banco_destino=banco,  # ← guardamos el banco usado
                        monto=monto,
                        moneda=cuenta_origen.moneda,
                        estado=Transaction.EstadoTransaccion.COMPLETADA,
                    )

                    messages.success(request, f"Transferencia a {banco.nombre} completada")
                    return redirect("dashboard")
                else:
                    messages.error(request, f"Error del banco destino: {response.status_code}")

            except requests.RequestException:
                messages.error(request, "No se pudo conectar al banco destino")

    else:
        form = TransferenciaExternaForm()
        form.fields["cuenta_origen"].choices = choices

    return render(request, "transferencia_externa.html", {"form": form})