from django import forms
from accounts.models import Account
from banks.models import Bank


class TransferenciaInternaForm(forms.Form):
    cuenta_origen = forms.ChoiceField(label="Cuenta Origen")
    numero_cuenta_destino = forms.CharField(label="Cuenta Destino")
    monto = forms.DecimalField(
        label="Monto", max_digits=12, decimal_places=2, min_value=0.01
    )

    def __init__(self, *args, cuenta_origen_obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._cuenta_origen_obj = cuenta_origen_obj

    def clean_monto(self):
        monto = self.cleaned_data.get("monto")
        if monto is not None and monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero.")
        return monto

    def clean_numero_cuenta_destino(self):
        numero_destino = self.cleaned_data.get("numero_cuenta_destino")
        if not Account.objects.filter(numero_cuenta=numero_destino).exists():
            raise forms.ValidationError(
                f"No existe ninguna cuenta con el número «{numero_destino}». "
                "Verificá el número e intentá de nuevo."
            )
        return numero_destino

    def clean(self):
        cleaned_data = super().clean()
        cuenta_origen_id = cleaned_data.get("cuenta_origen")
        numero_destino = cleaned_data.get("numero_cuenta_destino")
        monto = cleaned_data.get("monto")

        if cuenta_origen_id and numero_destino:
            try:
                cuenta_origen = Account.objects.get(id=cuenta_origen_id)

                if cuenta_origen.numero_cuenta == numero_destino:
                    raise forms.ValidationError(
                        "No podés transferir dinero a tu propia cuenta. "
                        "Seleccioná una cuenta destino diferente."
                    )

                if monto and cuenta_origen.saldo_actual < monto:
                    raise forms.ValidationError(
                        f"Saldo insuficiente. Tu saldo disponible es "
                        f"{cuenta_origen.saldo_actual:,.2f} {cuenta_origen.moneda} "
                        f"y estás intentando transferir {monto:,.2f} {cuenta_origen.moneda}."
                    )

            except Account.DoesNotExist:
                pass

        return cleaned_data


class TransferenciaExternaForm(forms.Form):
    cuenta_origen = forms.ChoiceField(label="Cuenta Origen")
    banco_destino = forms.ModelChoiceField(
        queryset=Bank.objects.filter(activo=True),
        label="Banco Destino",
        empty_label="-- Seleccionar banco --",
        error_messages={
            "required": "Debés seleccionar un banco destino.",
            "invalid_choice": "El banco seleccionado no es válido.",
        },
    )
    numero_cuenta_destino = forms.CharField(
        label="Número de Cuenta Destino",
        error_messages={"required": "Ingresá el número de cuenta destino."},
    )
    monto = forms.DecimalField(
        label="Monto",
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        error_messages={
            "required": "Ingresá el monto a transferir.",
            "min_value": "El monto mínimo a transferir es 0.01.",
            "invalid": "Ingresá un monto numérico válido.",
        },
    )

    def clean_monto(self):
        monto = self.cleaned_data.get("monto")
        if monto is not None and monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero.")
        return monto

    def clean(self):
        cleaned_data = super().clean()
        cuenta_origen_id = cleaned_data.get("cuenta_origen")
        monto = cleaned_data.get("monto")
        banco = cleaned_data.get("banco_destino")

        if cuenta_origen_id and monto:
            try:
                cuenta_origen = Account.objects.get(id=cuenta_origen_id)

                if cuenta_origen.saldo_actual < monto:
                    raise forms.ValidationError(
                        f"Saldo insuficiente. Tu saldo disponible es "
                        f"{cuenta_origen.saldo_actual:,.2f} {cuenta_origen.moneda} "
                        f"y estás intentando transferir {monto:,.2f} {cuenta_origen.moneda}."
                    )

            except Account.DoesNotExist:
                pass

        return cleaned_data
