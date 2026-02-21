import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from accounts.models import Account
from transactions.models import Transaction
from decimal import Decimal

@csrf_exempt
@require_POST
def recibir_transferencia(request):
    try:
        data = json.loads(request.body)

        numero_cuenta = data.get("cuenta_destino")
        # monto = float(data.get("monto"))
        monto = Decimal(str(data.get("monto")))  # Convertir a Decimal para precisión
        banco_origen = data.get("banco_origen")

        cuenta = Account.objects.get(numero_cuenta=numero_cuenta)

        if monto <= 0:
            return JsonResponse(
                {"status": "error", "message": "Monto inválido"}, status=400
            )

        cuenta.saldo_actual += monto
        cuenta.save()

        Transaction.objects.create(
            tipo_transaccion=Transaction.TipoTransaccion.EXTERNA,
            cuenta_origen=cuenta,  # Simulación simple
            monto=monto,
            moneda=cuenta.moneda,
            estado=Transaction.EstadoTransaccion.COMPLETADA,
        )

        return JsonResponse(
            {"status": "success", "message": "Transferencia recibida correctamente"}
        )

    except Account.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Cuenta no encontrada"}, status=404
        )

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
