from django.conf import settings
from django.db import models


class PerfilCliente(models.Model):
    ROLES = (
        ('cliente', 'Cliente'),
        ('admin', 'Administrador'),
    )

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil_cliente')
    telefono = models.CharField(max_length=20, unique=True, blank=True, null=True) # Ajustado a blank/null por si el login de Google no lo trae de entrada
    direccion = models.TextField(blank=True)
    rol = models.CharField(max_length=10, choices=ROLES, default='cliente')
    
    # Nuevos campos para la foto y avatar de Google
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)

    sms_code = models.CharField(max_length=128, blank=True)
    code_created_at = models.DateTimeField(null=True, blank=True)
    sms_code_attempts = models.PositiveSmallIntegerField(default=0)

    def get_avatar_url(self):
        """Retorna la imagen local, la de Google o un respaldo por defecto."""
        if self.avatar:
            return self.avatar.url
        elif self.avatar_url:
            return self.avatar_url
        return '/static/images/default_avatar.png'

    def __str__(self):
        return self.usuario.email or self.usuario.username
