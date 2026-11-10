from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string

from .models import Pedido


def enviar_confirmacion_pedido(pedido_id):
    with transaction.atomic():
        pedido = (
            Pedido.objects.select_for_update()
            .select_related('cliente')
            .prefetch_related('items__producto')
            .get(pk=pedido_id)
        )
        if pedido.estado != 'PAGADO':
            return False
        if pedido.confirmacion_email_enviada:
            return True
        if not pedido.cliente.email:
            raise ValueError(f'El pedido {pedido.pk} no tiene un correo de destinatario.')

        items = list(pedido.items.all())
        context = {'pedido': pedido, 'items': items}
        plain_items = '\n'.join(
            f'{item.producto.nombre} ({item.talla}) x {item.cantidad}: '
            f'${item.subtotal:,.2f}'
            for item in items
        )
        text_body = (
            f'Confirmación del pedido #{pedido.pk} - MH’ELEGANZA\n\n'
            f'{plain_items}\n\n'
            f'Total: ${pedido.total:,.2f}\n'
            f'Dirección de envío: {pedido.direccion_envio}\n'
            f'Estado del pago: {pedido.get_estado_display()}\n'
        )
        message = EmailMultiAlternatives(
            subject=f'Confirmación del pedido #{pedido.pk} - MH’ELEGANZA',
            body=text_body,
            from_email=None,
            to=[pedido.cliente.email],
        )
        message.attach_alternative(
            render_to_string('emails/order_confirmation.html', context),
            'text/html',
        )
        if message.send(fail_silently=False) != 1:
            raise RuntimeError(f'No se envió el correo de confirmación del pedido {pedido.pk}.')
        pedido.confirmacion_email_enviada = True
        pedido.save(update_fields=['confirmacion_email_enviada'])
    return True
