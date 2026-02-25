from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
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

    cliente = request.user.cliente
    cuentas = cliente.cuentas.all()
    transacciones = []

    for cuenta in cuentas:
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

    paginator = Paginator(transacciones, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "dashboard_cliente.html",
        {
            "cuentas": cuentas,
            "page_obj": page_obj,
        },
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

                if cuenta_origen.saldo_actual < monto:
                    messages.error(
                        request,
                        f"Saldo insuficiente. Disponible: {cuenta_origen.saldo_actual:,.2f} {cuenta_origen.moneda}.",
                    )
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

                messages.success(
                    request,
                    f"✓ Transferencia de {monto:,.2f} {cuenta_origen.moneda} "
                    f"a la cuenta {numero_destino} realizada correctamente.",
                )
                return redirect("dashboard")

            except Account.DoesNotExist:
                messages.error(
                    request,
                    f"No se encontró ninguna cuenta con el número «{numero_destino}».",
                )

    else:
        form = TransferenciaInternaForm()
        form.fields["cuenta_origen"].choices = choices

    return render(request, "transferencia_interna.html", {"form": form})


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
            banco = form.cleaned_data["banco_destino"]
            monto = form.cleaned_data["monto"]

            if cuenta_origen.saldo_actual < monto:
                messages.error(
                    request,
                    f"Saldo insuficiente. Disponible: {cuenta_origen.saldo_actual:,.2f} {cuenta_origen.moneda}.",
                )
                return redirect("transferencia_externa")

            try:
                response = requests.post(
                    banco.url_api,
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
                        banco_destino=banco,
                        monto=monto,
                        moneda=cuenta_origen.moneda,
                        estado=Transaction.EstadoTransaccion.COMPLETADA,
                    )

                    messages.success(
                        request,
                        f"✓ Transferencia de {monto:,.2f} {cuenta_origen.moneda} "
                        f"a {banco.nombre} (cuenta {numero_destino}) completada.",
                    )
                    return redirect("dashboard")

                else:
                    messages.error(
                        request,
                        f"El banco {banco.nombre} rechazó la transferencia "
                        f"(código {response.status_code}). No se descontó ningún monto.",
                    )

            except requests.ConnectionError:
                messages.error(
                    request,
                    f"No se pudo establecer conexión con {banco.nombre}. "
                    "Verificá que el banco esté disponible e intentá de nuevo.",
                )
            except requests.Timeout:
                messages.error(
                    request,
                    f"La conexión con {banco.nombre} tardó demasiado (timeout). "
                    "No se realizó ningún descuento. Intentá de nuevo más tarde.",
                )
            except requests.RequestException as e:
                messages.error(
                    request,
                    f"Error inesperado al conectar con {banco.nombre}: {str(e)}",
                )

    else:
        form = TransferenciaExternaForm()
        form.fields["cuenta_origen"].choices = choices

    return render(request, "transferencia_externa.html", {"form": form})
