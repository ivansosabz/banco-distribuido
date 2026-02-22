from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout


def home(request):
    return render(request, "home.html")


@login_required
def dashboard(request):
    if request.user.is_superuser:
        return render(request, "dashboard_admin.html")
    else:
        return render(request, "dashboard_cliente.html")
