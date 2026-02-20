import uuid
from django.db import models
from django.utils import timezone


class Client(models.Model):

    class TipoIdentificacion(models.TextChoices):
        CEDULA = "cedula", "Cédula"
        RUC = "ruc", "RUC"
        PASAPORTE = "pasaporte", "Pasaporte"

    class EstadoCliente(models.TextChoices):
        ACTIVO = "activo", "Activo"
        INACTIVO = "inactivo", "Inactivo"
        PENDIENTE = "pendiente_verificacion", "Pendiente Verificación"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tipo_identificacion = models.CharField(
        max_length=20, choices=TipoIdentificacion.choices
    )

    numero_identificacion = models.CharField(max_length=30, unique=True)

    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)

    fecha_nacimiento = models.DateField()

    nacionalidad = models.CharField(max_length=50, default="paraguaya")

    telefono = models.CharField(max_length=20)
    email = models.EmailField()

    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    estado = models.CharField(
        max_length=30, choices=EstadoCliente.choices, default=EstadoCliente.ACTIVO
    )

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.numero_identificacion}"
