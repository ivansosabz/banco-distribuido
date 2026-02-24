import json
import logging
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.models import Account
from transactions.models import Transaction

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def recibir_transferencia(request):
    try:
        data = json.loads(request.body)
        numero_cuenta = data.get("cuenta_destino")
        banco_origen = data.get("banco_origen")

        try:
            monto = Decimal(str(data.get("monto")))
        except (InvalidOperation, TypeError):
            return JsonResponse(
                {"status": "error", "message": "Monto inválido"}, status=400
            )

        if monto <= 0:
            return JsonResponse(
                {"status": "error", "message": "Monto inválido"}, status=400
            )

        cuenta = Account.objects.get(numero_cuenta=numero_cuenta)

        cuenta.saldo_actual += monto
        cuenta.save()

        Transaction.objects.create(
            tipo_transaccion=Transaction.TipoTransaccion.EXTERNA,
            cuenta_origen=None,
            cuenta_destino=cuenta,
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
    except Exception:
        logger.exception("Error inesperado en recibir_transferencia")
        return JsonResponse(
            {"status": "error", "message": "Error interno del servidor"}, status=500
        )
