import re

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.conf import settings
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from .forms import LoginForm, RegistroForm
from .models import PerfilCliente


# 1. Iniciar sesión
@ensure_csrf_cookie
@never_cache
def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST':
        identificador = form.data.get('identificador', '').strip()
        password = form.data.get('password', '')
        if form.is_valid():
            User = get_user_model()
            usuario_db = User.objects.filter(email__iexact=identificador).first()
            if usuario_db is None:
                perfil = PerfilCliente.objects.select_related('usuario').filter(telefono=identificador).first()
                usuario_db = perfil.usuario if perfil else None

            if usuario_db is None:
                form.add_error('identificador', 'Usuario no registrado')
            else:
                usuario = authenticate(request, username=usuario_db.get_username(), password=password)
                if usuario:
                    login(request, usuario)
                    perfil = getattr(usuario, 'perfil_cliente', None)
                    request.session['usuario'] = {
                        'nombre': usuario.get_full_name() or usuario.get_username(),
                        'email': usuario.email,
                        'telefono': perfil.telefono if perfil else '',
                        'rol': 'admin' if usuario.is_staff else (perfil.rol if perfil else 'cliente'),
                    }
                    request.session['direccion_usuario'] = perfil.direccion if perfil else ''
                    return redirect('admin_productos' if usuario.is_staff else 'catalogo')
                form.add_error('password', 'Contraseña incorrecta')

    cuentas_demo = None
    if settings.DEBUG:
        cuentas_demo = {
            'admin': {'usuario': 'admin@mheleganza.com', 'password': 'Admin123!'},
            'cliente': {'usuario': 'cliente@mheleganza.com', 'password': 'Cliente123!'},
        }
    return render(request, 'app_usuarios/login.html', {'form': form, 'cuentas_demo': cuentas_demo})

# 2. Registrar usuario
@ensure_csrf_cookie
@never_cache
def registro_view(request):
    form = RegistroForm(request.POST or None)
    campos_incompletos = request.method == 'POST' and any(
        not request.POST.get(campo, '').strip()
        for campo in ('nombre', 'email', 'telefono', 'password')
    )
    if request.method == 'POST':
        if form.is_valid():
            User = get_user_model()
            nombre = form.cleaned_data['nombre'].strip()
            email = form.cleaned_data['email']
            try:
                with transaction.atomic():
                    usuario = User.objects.create_user(
                        username=email,
                        email=email,
                        password=form.cleaned_data['password'],
                        first_name=nombre,
                    )
                    PerfilCliente.objects.create(
                        usuario=usuario,
                        telefono=form.cleaned_data['telefono'],
                        direccion=form.cleaned_data.get('direccion', '').strip(),
                    )
            except IntegrityError:
                form.add_error('email', 'El correo ya está registrado')
            else:
                messages.success(request, 'Registro exitoso')
                return redirect('catalogo')

    return render(request, 'app_usuarios/registro.html', {
        'form': form,
        'campos_incompletos': campos_incompletos,
    })

# 4. Ver perfil de datos
def perfil_datos_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    cuenta = request.user
    perfil = getattr(cuenta, 'perfil_cliente', None) if cuenta.is_authenticated else None
    usuario = request.session.get('usuario', {
        'nombre': cuenta.get_full_name() or cuenta.get_username(),
        'email': cuenta.email,
        'telefono': perfil.telefono if perfil else '',
        'rol': 'admin' if cuenta.is_staff else (perfil.rol if perfil else 'cliente'),
    })
    return render(request, 'app_usuarios/perfil_datos.html', {
        'usuario': usuario,
        'cuenta': cuenta,
        'perfil': perfil,
    })


def actualizar_perfil_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    perfil = getattr(request.user, 'perfil_cliente', None)
    if perfil is None:
        messages.error(request, 'No se encontró el perfil de esta cuenta.')
        return redirect('perfil_datos')
    error = None
    errores_campos = {'nombre': False, 'email': False, 'telefono': False}
    valores_perfil = {
        'nombre': request.user.first_name,
        'email': request.user.email,
        'telefono': perfil.telefono,
    }
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip().lower()
        telefono = request.POST.get('telefono', '').strip()
        valores_perfil = {'nombre': nombre, 'email': email, 'telefono': telefono}
        if not nombre or not email or not telefono:
            error = 'Campos incompletos'
            errores_campos = {
                'nombre': not bool(nombre),
                'email': not bool(email),
                'telefono': not bool(telefono),
            }
        else:
            try:
                validate_email(email)
            except ValidationError:
                error = 'Correo no válido'
                errores_campos['email'] = True
            if not error and get_user_model().objects.filter(email__iexact=email).exclude(pk=request.user.pk).exists():
                error = 'Correo existente'
                errores_campos['email'] = True
            if not error and PerfilCliente.objects.filter(telefono=telefono).exclude(pk=perfil.pk).exists():
                error = 'El teléfono ya está registrado.'
                errores_campos['telefono'] = True
        if not error:
            request.user.first_name = nombre
            request.user.email = email
            request.user.username = email
            request.user.save(update_fields=['first_name', 'email', 'username'])
            perfil.telefono = telefono
            perfil.save(update_fields=['telefono'])
            if 'usuario' in request.session:
                request.session['usuario'].update({'nombre': nombre, 'email': email, 'telefono': telefono})
            messages.success(request, 'Actualización exitosa')
            return redirect('perfil_datos')
    return render(request, 'app_usuarios/actualizar_perfil.html', {
        'cuenta': request.user,
        'perfil': perfil,
        'error': error,
        'errores_campos': errores_campos,
        'valores_perfil': valores_perfil,
    })

# 5. Actualizar dirección
def actualizar_direccion_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        nueva_direccion = request.POST.get('direccion', '').strip()
        if nueva_direccion:
            perfil = getattr(request.user, 'perfil_cliente', None) if request.user.is_authenticated else None
            if perfil:
                perfil.direccion = nueva_direccion
                perfil.save(update_fields=['direccion'])
            request.session['direccion_usuario'] = nueva_direccion
            messages.success(request, 'Actualización exitosa')
            return redirect('perfil_datos')

    return render(request, 'app_usuarios/actualizar_direccion.html', {
        'direccion_actual': request.session.get('direccion_usuario', '')
    })

# 6. Actualizar contraseña
def actualizar_contrasena_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    mensaje = None
    error = None
    if request.method == 'POST':
        actual = request.POST.get('password_actual', '')
        nueva = request.POST.get('password_nuevo', '')
        if not request.user.check_password(actual):
            error = 'Contraseña incorrecta'
        elif len(nueva) < 8:
            error = 'La contraseña debe tener mínimo 8 caracteres'
        elif not re.search(r'[A-Z]', nueva) or not re.search(r'[a-z]', nueva) or not re.search(r'[0-9]', nueva) or not re.search(r'[\W_]', nueva):
            error = 'La contraseña debe incluir mayúscula, minúscula, número y carácter especial.'
        else:
            request.user.set_password(nueva)
            request.user.save(update_fields=['password'])
            update_session_auth_hash(request, request.user)
            mensaje = 'Contraseña actualizada exitosamente'

    return render(request, 'app_usuarios/actualizar_contrasena.html', {
        'mensaje': mensaje,
        'error': error,
    })

# 7. Cerrar sesión (Requerida por app_usuarios/urls.py)
def cerrar_sesion_view(request):
    logout(request)
    request.session.flush()
    return redirect('login')