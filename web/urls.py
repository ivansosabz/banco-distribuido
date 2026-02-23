from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("transferencia/", views.transferencia_interna, name="transferencia_interna"),
    path(
        "transferencia-externa/",
        views.transferencia_externa,
        name="transferencia_externa",
    ),
]
