import logging
from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from app_inventario.models import Inventario
from app_productos.models import Producto, VarianteProducto

from .models import DetallePedido, Pedido

logger = logging.getLogger(__name__)

ZERO_DECIMAL_CURRENCIES = {
    'bif', 'clp', 'djf', 'gnf', 'jpy', 'kmf', 'krw', 'mga', 'pyg',
    'rwf', 'ugx', 'vnd', 'vuv', 'xaf', 'xof', 'xpf',
}


class CheckoutValidationError(ValueError):
    pass


def _stripe_amount(price, currency):
    exponent = 0 if currency in ZERO_DECIMAL_CURRENCIES else 2
    multiplier = Decimal(10) ** exponent
    amount = Decimal(price) * multiplier
    if amount != amount.to_integral_value() or amount <= 0:
        raise CheckoutValidationError('El precio del producto no es válido para Stripe.')
    return int(amount)


def _validated_cart_lines(cart):
    if not isinstance(cart, dict) or not cart:
        raise CheckoutValidationError('Tu carrito está vacío.')

    parsed = []
    try:
        for item in cart.values():
            product_id = int(item['producto_id'])
            quantity = int(item['cantidad'])
            variant_id = item.get('variante_id')
            parsed.append((product_id, int(variant_id) if variant_id else None, quantity))
    except (KeyError, TypeError, ValueError):
        raise CheckoutValidationError('El carrito contiene productos no válidos.') from None

    if any(quantity < 1 for _, _, quantity in parsed):
        raise CheckoutValidationError('El carrito contiene cantidades no válidas.')
    return sorted(parsed)


@login_required(login_url='login')
def crear_checkout_stripe(request, direccion):
    if not settings.STRIPE_SECRET_KEY:
        return None, 'El pago con tarjeta no está disponible en este momento.'

    cart = request.session.get('carrito', {})
    currency = settings.STRIPE_CURRENCY.lower()
    try:
        parsed_lines = _validated_cart_lines(cart)
        with transaction.atomic():
            lines = []
            product_reservations = {}
            variant_reservations = {}
            for product_id, variant_id, quantity in parsed_lines:
                producto = Producto.objects.select_for_update().filter(
                    pk=product_id,
                    disponible=True,
                ).first()
                if producto is None:
                    raise CheckoutValidationError('Producto no disponible.')
                inventario = Inventario.objects.select_for_update().filter(producto=producto).first()
                if inventario is None:
                    raise CheckoutValidationError('Producto no disponible.')

                variante = None
                if variant_id:
                    variante = VarianteProducto.objects.select_for_update().filter(
                        pk=variant_id,
                        producto=producto,
                    ).first()
                    if variante is None:
                        raise CheckoutValidationError('Producto no disponible.')
                else:
                    variante = VarianteProducto.objects.select_for_update().filter(
                        producto=producto,
                        talla=producto.talla,
                    ).first()

                product_reserved = product_reservations.get(producto.pk, 0)
                variant_reserved = variant_reservations.get(variante.pk, 0) if variante else 0
                if (
                    inventario.stock_actual - product_reserved < quantity
                    or (variante and variante.stock - variant_reserved < quantity)
                ):
                    raise CheckoutValidationError('Producto no disponible.')

                product_reservations[producto.pk] = product_reserved + quantity
                if variante:
                    variant_reservations[variante.pk] = variant_reserved + quantity
                lines.append((producto, variante, quantity, producto.precio))

            total = sum((price * quantity for _, _, quantity, price in lines), Decimal('0.00'))
            line_items = [
                {
                    'price_data': {
                        'currency': currency,
                        'product_data': {'name': producto.nombre[:250]},
                        'unit_amount': _stripe_amount(price, currency),
                    },
                    'quantity': quantity,
                }
                for producto, _, quantity, price in lines
            ]
            pedido = Pedido.objects.create(
                cliente=request.user,
                metodo_pago='TARJETA',
                total=total,
                direccion_envio=direccion,
                estado='PENDIENTE',
            )
            for producto, variante, quantity, price in lines:
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    talla=variante.talla if variante else producto.talla,
                    cantidad=quantity,
                    precio_unitario=price,
                )

    except CheckoutValidationError as error:
        return None, str(error)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        checkout_session = stripe.checkout.Session.create(
            mode='payment',
            payment_method_types=['card'],
            line_items=line_items,
            customer_email=request.user.email or None,
            client_reference_id=str(pedido.pk),
            metadata={'pedido_id': str(pedido.pk)},
            success_url=(
                request.build_absolute_uri(reverse('payment_success'))
                + '?session_id={CHECKOUT_SESSION_ID}'
            ),
            cancel_url=(
                request.build_absolute_uri(reverse('payment_cancel'))
                + f'?order_id={pedido.pk}'
            ),
            api_key=settings.STRIPE_SECRET_KEY,
            idempotency_key=f'mheleganza-checkout-{pedido.pk}',
        )
        if not checkout_session.url:
            raise stripe.StripeError('Stripe did not return a Checkout URL.')
        Pedido.objects.filter(pk=pedido.pk).update(
            stripe_checkout_session_id=checkout_session.id,
        )
    except stripe.StripeError:
        logger.exception('Stripe Checkout session creation failed for order %s', pedido.pk)
        return None, 'No fue posible iniciar el pago. Inténtalo nuevamente.'

    return redirect(checkout_session.url), None


@login_required(login_url='login')
@require_GET
def payment_success(request):
    session_id = request.GET.get('session_id', '').strip()
    pedido = get_object_or_404(
        Pedido.objects.prefetch_related('items__producto'),
        stripe_checkout_session_id=session_id,
        cliente=request.user,
    )
    if pedido.estado == 'PAGADO':
        request.session['carrito'] = {}
        request.session.modified = True
    return render(request, 'app_pedido/payment_success.html', {'pedido': pedido})


@login_required(login_url='login')
@require_GET
def payment_cancel(request):
    return render(request, 'app_pedido/payment_cancel.html')
