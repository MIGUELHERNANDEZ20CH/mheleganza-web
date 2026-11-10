import logging
from smtplib import SMTPException

import stripe
from django.conf import settings
from django.db import DatabaseError, transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from app_inventario.models import Inventario, MovimientoInventario, NotificacionInventario
from app_productos.models import Producto, VarianteProducto

from .models import Pedido
from .services import enviar_confirmacion_pedido
from .views_checkout import _stripe_amount

logger = logging.getLogger(__name__)


def _value(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _payment_intent_id(session):
    payment_intent = _value(session, 'payment_intent')
    if isinstance(payment_intent, str):
        return payment_intent
    return _value(payment_intent, 'id') if payment_intent else None


def _refund(payment_intent_id, pedido_id):
    if not settings.STRIPE_SECRET_KEY or not payment_intent_id:
        raise RuntimeError('No se puede reembolsar el pago confirmado por Stripe.')
    stripe.Refund.create(
        payment_intent=payment_intent_id,
        api_key=settings.STRIPE_SECRET_KEY,
        idempotency_key=f'mheleganza-stock-refund-{pedido_id}',
    )


def _confirmar_pago(session):
    session_id = _value(session, 'id')
    metadata = _value(session, 'metadata', {}) or {}
    pedido_id = _value(metadata, 'pedido_id') or _value(session, 'client_reference_id')
    payment_intent_id = _payment_intent_id(session)
    if not session_id or not pedido_id:
        raise ValueError('La sesión de Stripe no contiene referencias de pedido válidas.')

    try:
        with transaction.atomic():
            pedido = (
                Pedido.objects.select_for_update()
                .filter(pk=pedido_id)
                .first()
            )
            if pedido is None or pedido.stripe_checkout_session_id != session_id:
                raise ValueError('No se encontró el pedido asociado a la sesión de Stripe.')

            amount_total = _value(session, 'amount_total')
            currency = (_value(session, 'currency', '') or '').lower()
            expected_amount = _stripe_amount(pedido.total, settings.STRIPE_CURRENCY.lower())
            payment_matches = (
                amount_total == expected_amount
                and currency == settings.STRIPE_CURRENCY.lower()
                and _value(session, 'payment_status') == 'paid'
            )
            if pedido.estado == 'PAGADO':
                refund_required = False
            elif pedido.estado == 'RECHAZADO' or not payment_matches:
                pedido.estado = 'RECHAZADO'
                pedido.stripe_payment_intent_id = payment_intent_id or ''
                pedido.save(update_fields=['estado', 'stripe_payment_intent_id'])
                refund_required = True
            else:
                details = list(
                    pedido.items.select_related('producto').order_by('producto_id', 'talla', 'pk')
                )
                inventory_by_product = {}
                product_by_id = {}
                variant_by_key = {}
                product_reservations = {}
                variant_reservations = {}
                available = True

                for detail in details:
                    producto = Producto.objects.select_for_update().filter(
                        pk=detail.producto_id,
                        disponible=True,
                    ).first()
                    inventario = Inventario.objects.select_for_update().filter(
                        producto_id=detail.producto_id,
                    ).first()
                    variant_key = (detail.producto_id, detail.talla)
                    variante = VarianteProducto.objects.select_for_update().filter(
                        producto_id=detail.producto_id,
                        talla=detail.talla,
                    ).first()
                    if producto is None or inventario is None:
                        available = False
                        break
                    product_by_id[producto.pk] = producto
                    inventory_by_product[producto.pk] = inventario
                    product_reserved = product_reservations.get(producto.pk, 0)
                    variant_reserved = variant_reservations.get(variant_key, 0)
                    if (
                        inventario.stock_actual - product_reserved < detail.cantidad
                        or (
                            variante
                            and variante.stock - variant_reserved < detail.cantidad
                        )
                    ):
                        available = False
                        break
                    product_reservations[producto.pk] = product_reserved + detail.cantidad
                    if variante:
                        variant_reservations[variant_key] = variant_reserved + detail.cantidad
                        variant_by_key[variant_key] = variante

                if not available:
                    pedido.estado = 'RECHAZADO'
                    pedido.stripe_payment_intent_id = payment_intent_id or ''
                    pedido.save(update_fields=['estado', 'stripe_payment_intent_id'])
                    refund_required = True
                else:
                    for detail in details:
                        producto = product_by_id[detail.producto_id]
                        inventario = inventory_by_product[detail.producto_id]
                        variant_key = (detail.producto_id, detail.talla)
                        variante = variant_by_key.get(variant_key)
                        if variante:
                            variante.stock -= detail.cantidad
                            variante.save(update_fields=['stock'])
                        inventario.stock_actual -= detail.cantidad
                        inventario.save(update_fields=['stock_actual', 'actualizado_en'])
                        MovimientoInventario.objects.create(
                            producto=producto,
                            tipo='VENTA',
                            cantidad=detail.cantidad,
                            stock_resultante=inventario.stock_actual,
                        )
                        if inventario.stock_actual == 0:
                            producto.disponible = False
                            producto.save(update_fields=['disponible'])
                            NotificacionInventario.objects.create(
                                producto=producto,
                                mensaje=f'{producto.nombre} se quedó sin unidades disponibles.',
                            )
                    pedido.estado = 'PAGADO'
                    pedido.stripe_payment_intent_id = payment_intent_id or ''
                    pedido.save(update_fields=['estado', 'stripe_payment_intent_id'])
                    refund_required = False
    except DatabaseError:
        logger.exception('Database failure processing Stripe Checkout session %s', session_id)
        raise
    if refund_required:
        _refund(payment_intent_id, pedido_id)
        return
    enviar_confirmacion_pedido(pedido_id)


def _marcar_pago_fallido(session):
    session_id = _value(session, 'id')
    metadata = _value(session, 'metadata', {}) or {}
    pedido_id = _value(metadata, 'pedido_id') or _value(session, 'client_reference_id')
    if not session_id or not pedido_id:
        raise ValueError('El evento fallido no contiene referencias de pedido válidas.')
    Pedido.objects.filter(
        pk=pedido_id,
        stripe_checkout_session_id=session_id,
        estado='PENDIENTE',
    ).update(estado='RECHAZADO')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error('STRIPE_WEBHOOK_SECRET is not configured.')
        return HttpResponse('Webhook no configurado.', status=503)

    signature = request.headers.get('Stripe-Signature', '')
    try:
        event = stripe.Webhook.construct_event(
            request.body,
            signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponse('Firma de webhook inválida.', status=400)

    event_type = _value(event, 'type', '')
    session = _value(_value(event, 'data', {}), 'object', {})
    try:
        if event_type == 'checkout.session.completed':
            if _value(session, 'payment_status') == 'paid':
                _confirmar_pago(session)
        elif event_type == 'checkout.session.async_payment_succeeded':
            _confirmar_pago(session)
        elif event_type == 'checkout.session.async_payment_failed':
            _marcar_pago_fallido(session)
        elif event_type == 'checkout.session.expired':
            _marcar_pago_fallido(session)
        else:
            return HttpResponse(status=200)
    except stripe.StripeError:
        logger.exception('Stripe API operation failed while processing webhook.')
        return HttpResponse('No fue posible procesar el pago.', status=500)
    except (ValueError, TypeError):
        logger.exception('Invalid Stripe webhook payload.')
        return HttpResponse('Evento de pago no válido.', status=400)
    except (DatabaseError, OSError, SMTPException, RuntimeError):
        logger.exception('Temporary failure while processing Stripe webhook.')
        return HttpResponse('Error temporal al procesar el pago.', status=500)
    return HttpResponse(status=200)
