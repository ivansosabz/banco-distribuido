from django import forms
from accounts.models import Account
from banks.models import Bank


class TransferenciaInternaForm(forms.Form):
    cuenta_origen = forms.ChoiceField(label="Cuenta Origen")
    numero_cuenta_destino = forms.CharField(label="Cuenta Destino")
    monto = forms.DecimalField(label="Monto", max_digits=12, decimal_places=2, min_value=0.01)

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
            raise forms.ValidationError("La cuenta destino no existe.")
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
                    raise forms.ValidationError("No puedes transferir a tu propia cuenta.")
                if monto and cuenta_origen.saldo_actual < monto:
                    raise forms.ValidationError(
                        f"Saldo insuficiente. Saldo disponible: {cuenta_origen.saldo_actual} {cuenta_origen.moneda}."
                    )
            except Account.DoesNotExist:
                pass

        return cleaned_data


class TransferenciaExternaForm(forms.Form):
    cuenta_origen = forms.ChoiceField(label="Cuenta Origen")
    # ← NUEVO: dropdown de bancos en lugar de campo URL libre
    banco_destino = forms.ModelChoiceField(
        queryset=Bank.objects.filter(activo=True),
        label="Banco Destino",
        empty_label="-- Seleccionar banco --",
    )
    numero_cuenta_destino = forms.CharField(label="Número de Cuenta Destino")
    monto = forms.DecimalField(label="Monto", max_digits=12, decimal_places=2, min_value=0.01)

    def clean_monto(self):
        monto = self.cleaned_data.get("monto")
        if monto is not None and monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero.")
        return monto

    def clean(self):
        cleaned_data = super().clean()
        cuenta_origen_id = cleaned_data.get("cuenta_origen")
        monto = cleaned_data.get("monto")

        if cuenta_origen_id and monto:
            try:
                cuenta_origen = Account.objects.get(id=cuenta_origen_id)
                if cuenta_origen.saldo_actual < monto:
                    raise forms.ValidationError(
                        f"Saldo insuficiente. Saldo disponible: {cuenta_origen.saldo_actual} {cuenta_origen.moneda}."
                    )
            except Account.DoesNotExist:
                pass

        return cleaned_data