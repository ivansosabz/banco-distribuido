from django.urls import path
from .views import recibir_transferencia

urlpatterns = [
    path("receive-transfer/", recibir_transferencia),
]
