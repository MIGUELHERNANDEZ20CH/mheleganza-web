import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import PerfilCliente


class RegistroForm(forms.Form):
    nombre = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'})
    )
    email = forms.EmailField(
        max_length=150,
        required=True,
        error_messages={'required': 'Campos incompletos', 'invalid': 'Correo no válido'},
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'})
    )
    telefono = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'})
    )
    direccion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Dirección de envío', 'rows': 2})
    )
    password = forms.CharField(
        required=True,
        error_messages={'required': 'Campos incompletos'},
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise ValidationError("El correo ya está registrado")
        return email.lower()

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono'].strip()
        if PerfilCliente.objects.filter(telefono=telefono).exists():
            raise ValidationError("El teléfono ya está registrado.")
        return telefono

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise ValidationError("La contraseña debe tener mínimo 8 caracteres")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("La contraseña debe incluir una letra mayúscula")
        if not re.search(r'[a-z]', password):
            raise ValidationError("La contraseña debe incluir una letra minúscula")
        if not re.search(r'[0-9]', password):
            raise ValidationError("La contraseña debe incluir un número")
        if not re.search(r'[\W_]', password):
            raise ValidationError("La contraseña debe incluir un carácter especial")
        return password


class LoginForm(forms.Form):
    """Formulario para la HU02 (Inicio de sesión por correo o teléfono y contraseña)."""
    identificador = forms.CharField(
        label='Usuario',
        required=True,
        error_messages={'required': 'Campos obligatorios'},
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico o teléfono',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        label='Contraseña',
        required=True,
        error_messages={'required': 'Campos obligatorios'},
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña',
            'autocomplete': 'current-password',
        })
    )