from django.conf import settings
from django.db import models


class PerfilCliente(models.Model):
	ROLES = (
		('cliente', 'Cliente'),
		('admin', 'Administrador'),
	)

	usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil_cliente')
	telefono = models.CharField(max_length=20, unique=True)
	direccion = models.TextField(blank=True)
	rol = models.CharField(max_length=10, choices=ROLES, default='cliente')
	sms_code = models.CharField(max_length=128, blank=True)
	code_created_at = models.DateTimeField(null=True, blank=True)
	sms_code_attempts = models.PositiveSmallIntegerField(default=0)

	def __str__(self):
		return self.usuario.email or self.usuario.username
