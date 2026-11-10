import logging
import re
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from twilio.base.exceptions import TwilioException

from .models import PerfilCliente
from .services import (
    enviar_sms,
    guardar_hash_codigo,
    normalize_phone_number,
    validar_codigo,
)

logger = logging.getLogger(__name__)
GENERIC_SMS_MESSAGE = 'Si el número está asociado a una cuenta, recibirás un código de recuperación.'


@require_http_methods(['GET', 'POST'])
def request_phone_reset(request):
    error = None
    if request.method == 'POST':
        submitted_phone = request.POST.get('telefono', '').strip()
        if not submitted_phone:
            error = 'Ingresa el número telefónico registrado.'
        else:
            try:
                normalized_phone = normalize_phone_number(submitted_phone)
            except ValueError:
                normalized_phone = ''
            digits = re.sub(r'\D', '', submitted_phone)
            local_digits = digits
            country_code = settings.TWILIO_DEFAULT_COUNTRY_CODE
            if country_code and digits.startswith(country_code):
                local_digits = digits[len(country_code):]
            profile = PerfilCliente.objects.select_related('usuario').filter(
                telefono__in={submitted_phone, digits, local_digits, normalized_phone},
            ).first() if normalized_phone else None
            if profile:
                try:
                    destination = normalize_phone_number(profile.telefono)
                    code = f'{secrets.randbelow(1_000_000):06d}'
                    should_send = False
                    with transaction.atomic():
                        profile = PerfilCliente.objects.select_for_update().get(pk=profile.pk)
                        recent = (
                            profile.code_created_at
                            and timezone.now() - profile.code_created_at
                            < timedelta(seconds=settings.SMS_OTP_RESEND_SECONDS)
                        )
                        if not recent:
                            profile.sms_code = guardar_hash_codigo(code)
                            profile.code_created_at = timezone.now()
                            profile.sms_code_attempts = 0
                            profile.save(update_fields=[
                                'sms_code', 'code_created_at', 'sms_code_attempts',
                            ])
                            should_send = True
                    if should_send:
                        try:
                            enviar_sms(
                                destination,
                                f'Tu código de recuperación MH’ELEGANZA es {code}. '
                                f'Vence en {settings.SMS_OTP_TTL_SECONDS // 60} minutos.',
                            )
                        except (RuntimeError, ValueError, TwilioException, OSError):
                            logger.exception('Could not send SMS password-reset code.')
                            PerfilCliente.objects.filter(pk=profile.pk).update(
                                sms_code='',
                                code_created_at=None,
                                sms_code_attempts=0,
                            )
                        else:
                            request.session['sms_reset_profile_id'] = profile.pk
                    else:
                        request.session['sms_reset_profile_id'] = profile.pk
                except ValueError:
                    logger.warning('Invalid phone number stored for profile %s.', profile.pk)
    return render(request, 'app_usuarios/request_phone_reset.html', {
        'error': error,
        'generic_message': GENERIC_SMS_MESSAGE if request.method == 'POST' and not error else '',
    })


@require_http_methods(['GET', 'POST'])
def verify_phone_code(request):
    error = None
    if request.method == 'POST':
        profile_id = request.session.get('sms_reset_profile_id')
        code = request.POST.get('codigo', '').strip()
        if not code.isdigit() or len(code) != 6:
            error = 'Ingresa el código de seis dígitos.'
        else:
            with transaction.atomic():
                profile = (
                    PerfilCliente.objects.select_for_update()
                    .select_related('usuario')
                    .filter(pk=profile_id)
                    .first()
                )
                valid_window = bool(
                    profile
                    and profile.code_created_at
                    and timezone.now() - profile.code_created_at
                    <= timedelta(seconds=settings.SMS_OTP_TTL_SECONDS)
                )
                valid_attempts = bool(
                    profile and profile.sms_code_attempts < settings.SMS_OTP_MAX_ATTEMPTS
                )
                if (
                    not profile
                    or not valid_window
                    or not valid_attempts
                    or not validar_codigo(code, profile.sms_code)
                ):
                    if profile and valid_window and valid_attempts:
                        profile.sms_code_attempts += 1
                        if profile.sms_code_attempts >= settings.SMS_OTP_MAX_ATTEMPTS:
                            profile.sms_code = ''
                        profile.save(update_fields=[
                            'sms_code_attempts', 'sms_code', 'code_created_at',
                        ])
                    error = 'Código inválido o vencido. Solicita uno nuevo.'
                else:
                    request.session.cycle_key()
                    request.session['sms_reset_verified_user_id'] = profile.usuario_id
                    request.session['sms_reset_verified_at'] = timezone.now().timestamp()
                    request.session.pop('sms_reset_profile_id', None)
                    profile.sms_code = ''
                    profile.code_created_at = None
                    profile.sms_code_attempts = 0
                    profile.save(update_fields=[
                        'sms_code', 'code_created_at', 'sms_code_attempts',
                    ])
                    return redirect('set_new_password')
    return render(request, 'app_usuarios/verify_phone_code.html', {'error': error})


@require_http_methods(['GET', 'POST'])
def set_new_password(request):
    user_id = request.session.get('sms_reset_verified_user_id')
    verified_at = request.session.get('sms_reset_verified_at', 0)
    if (
        not user_id
        or timezone.now().timestamp() - verified_at > settings.SMS_OTP_TTL_SECONDS
    ):
        request.session.pop('sms_reset_verified_user_id', None)
        request.session.pop('sms_reset_verified_at', None)
        messages.error(request, 'La verificación venció. Solicita un nuevo código.')
        return redirect('request_phone_reset')

    usuario = get_user_model().objects.filter(pk=user_id).first()
    if usuario is None:
        request.session.pop('sms_reset_verified_user_id', None)
        request.session.pop('sms_reset_verified_at', None)
        return redirect('request_phone_reset')

    error = None
    if request.method == 'POST':
        password = request.POST.get('password_nueva', '')
        confirmation = request.POST.get('password_confirmacion', '')
        if password != confirmation:
            error = 'Las contraseñas no coinciden.'
        else:
            try:
                password_validation.validate_password(password, usuario)
            except ValidationError as validation_error:
                error = ' '.join(validation_error.messages)
            else:
                usuario.set_password(password)
                usuario.save(update_fields=['password'])
                request.session.pop('sms_reset_profile_id', None)
                request.session.pop('sms_reset_verified_user_id', None)
                request.session.pop('sms_reset_verified_at', None)
                messages.success(request, 'Contraseña actualizada exitosamente.')
                return redirect('login')
    return render(request, 'app_usuarios/set_new_password.html', {'error': error})
