from django import forms


class TransferenciaInternaForm(forms.Form):
    cuenta_origen = forms.ChoiceField(label="Cuenta Origen")
    numero_cuenta_destino = forms.CharField(label="Cuenta Destino")
    monto = forms.DecimalField(label="Monto", max_digits=12, decimal_places=2)

class TransferenciaExternaForm(forms.Form):
    cuenta_origen = forms.ChoiceField(label="Cuenta Origen")
    numero_cuenta_destino = forms.CharField(label="Cuenta Destino Externa")
    url_banco_destino = forms.CharField(label="URL Banco Destino")
    monto = forms.DecimalField(label="Monto", max_digits=12, decimal_places=2)
