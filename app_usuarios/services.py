import re

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from twilio.rest import Client


def normalize_phone_number(phone_number):
    value = phone_number.strip()
    if value.startswith('+'):
        digits = re.sub(r'\D', '', value[1:])
    else:
        digits = re.sub(r'\D', '', value)
        if digits.startswith('00'):
            digits = digits[2:]
        elif settings.TWILIO_DEFAULT_COUNTRY_CODE and not digits.startswith(
            settings.TWILIO_DEFAULT_COUNTRY_CODE
        ):
            digits = f'{settings.TWILIO_DEFAULT_COUNTRY_CODE}{digits}'

    if not digits.isdigit() or not 8 <= len(digits) <= 15 or digits.startswith('0'):
        raise ValueError('El teléfono no tiene un formato internacional válido.')
    return f'+{digits}'


def guardar_hash_codigo(codigo):
    return make_password(codigo)


def validar_codigo(codigo, codigo_hash):
    return bool(codigo_hash) and check_password(codigo, codigo_hash)


def enviar_sms(telefono, mensaje):
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        raise RuntimeError('Twilio no está configurado.')
    if not settings.TWILIO_FROM_NUMBER and not settings.TWILIO_MESSAGING_SERVICE_SID:
        raise RuntimeError('Configura un número o Messaging Service de Twilio.')

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    options = {'to': normalize_phone_number(telefono), 'body': mensaje}
    if settings.TWILIO_MESSAGING_SERVICE_SID:
        options['messaging_service_sid'] = settings.TWILIO_MESSAGING_SERVICE_SID
    else:
        options['from_'] = normalize_phone_number(settings.TWILIO_FROM_NUMBER)
    return client.messages.create(**options)
