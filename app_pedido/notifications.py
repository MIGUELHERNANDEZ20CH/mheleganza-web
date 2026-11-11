import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from .models import Pedido

logger = logging.getLogger(__name__)

STATUS_MESSAGES = {
    'PENDIENTE': 'está pendiente de pago.',
    'PAGADO': 'tu pago fue confirmado.',
    'ENVIADO': 'tu pedido fue enviado.',
    'ENTREGADO': 'tu pedido fue entregado.',
    'RECHAZADO': 'tu pedido fue cancelado o el pago fue rechazado.',
}


def _admin_recipients():
    if settings.ADMIN_EMAIL:
        return [settings.ADMIN_EMAIL]

    recipients = [email for _, email in settings.ADMINS if email]
    if not recipients:
        recipients = list(
            get_user_model().objects.filter(
                is_active=True,
                is_staff=True,
            ).exclude(email='').values_list('email', flat=True)
        )
    return list(dict.fromkeys(recipients))


def enviar_alerta_nuevo_pedido(pedido_id):
    try:
        pedido = (
            Pedido.objects.select_related('cliente')
            .prefetch_related('items__producto')
            .get(pk=pedido_id)
        )
        destinatarios = _admin_recipients()
        if not destinatarios:
            logger.warning(
                'No se envió la alerta del pedido %s: no hay emails de administrador configurados.',
                pedido_id,
            )
            return

        cliente = pedido.cliente.get_full_name() or pedido.cliente.username
        lineas = [
            (
                f'- {item.producto.nombre} (talla {item.talla or "N/A"}) x '
                f'{item.cantidad} @ ${item.precio_unitario:,.2f} = '
                f'${item.subtotal:,.2f}'
            )
            for item in pedido.items.all()
        ]
        fecha = timezone.localtime(pedido.fecha_creacion).strftime('%Y-%m-%d %H:%M:%S %Z')
        cuerpo = (
            f'Se confirmó un nuevo pedido en MH’ELEGANZA.\n\n'
            f'Número de orden: #{pedido.pk}\n'
            f'Cliente: {cliente}\n'
            f'Correo del cliente: {pedido.cliente.email or "No registrado"}\n'
            f'Fecha: {fecha}\n'
            f'Estado: {pedido.get_estado_display()}\n\n'
            'Productos:\n'
            f'{"\n".join(lineas) if lineas else "- Sin productos"}\n\n'
            f'Total: ${pedido.total:,.2f}\n'
            f'Dirección de envío: {pedido.direccion_envio}'
        )
        enviados = send_mail(
            f'Nuevo pedido #{pedido.pk} - MH’ELEGANZA',
            cuerpo,
            settings.DEFAULT_FROM_EMAIL,
            destinatarios,
            fail_silently=False,
        )
        if enviados != len(destinatarios):
            logger.error(
                'Alerta del pedido %s enviada a %s de %s administradores.',
                pedido_id,
                enviados,
                len(destinatarios),
            )
    except Exception:
        logger.exception('Error al enviar alerta de nuevo pedido %s.', pedido_id)


def enviar_aviso_cambio_estado_pedido(pedido_id, estado_anterior, estado_nuevo):
    try:
        pedido = Pedido.objects.select_related('cliente').get(pk=pedido_id)
        email = pedido.cliente.email
        if not email:
            logger.warning(
                'No se envió el cambio de estado del pedido %s: el cliente no tiene email.',
                pedido_id,
            )
            return

        estado_anterior_display = dict(Pedido.ESTADOS).get(estado_anterior, estado_anterior)
        estado_nuevo_display = dict(Pedido.ESTADOS).get(estado_nuevo, estado_nuevo)
        asunto = f'Actualización del pedido #{pedido.pk}: {estado_nuevo_display}'
        nombre_cliente = pedido.cliente.get_full_name() or pedido.cliente.username
        mensaje = (
            f'Hola {nombre_cliente},\n\n'
            f'El estado de tu pedido #{pedido.pk} cambió de '
            f'{estado_anterior_display} a {estado_nuevo_display}.\n'
            f'{STATUS_MESSAGES.get(estado_nuevo, "El estado de tu pedido fue actualizado.")}\n\n'
            f'Total: ${pedido.total:,.2f}\n'
            f'Dirección de envío: {pedido.direccion_envio}\n\n'
            'Gracias por comprar en MH’ELEGANZA.'
        )
        enviados = send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        if enviados != 1:
            logger.error('No se pudo enviar el aviso de estado del pedido %s.', pedido_id)
    except Exception:
        logger.exception('Error al enviar aviso de cambio de estado del pedido %s.', pedido_id)
