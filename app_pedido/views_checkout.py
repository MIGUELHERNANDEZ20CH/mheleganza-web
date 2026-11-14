import logging
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from app_inventario.models import Inventario
from app_productos.models import Producto, VarianteProducto

from .models import DetallePedido, Pedido

logger = logging.getLogger(__name__)


class CheckoutValidationError(ValueError):
    pass


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
def crear_pedido_interno(request, direccion):
    """
    Procesa el checkout de forma interna (por ejemplo, pago contraentrega o transferencia manual),
    validando stock de manera atómica y creando el pedido.
    """
    cart = request.session.get('carrito', {})
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
            
            # Crear el pedido de forma interna
            pedido = Pedido.objects.create(
                cliente=request.user,
                metodo_pago='CONTRAENTREGA',
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
                
                # Opcional: Descontar stock inmediatamente del inventario
                inventario_obj = Inventario.objects.get(producto=producto)
                inventario_obj.stock_actual -= quantity
                inventario_obj.save()

    except CheckoutValidationError as error:
        return None, str(error)

    # Limpiar el carrito de la sesión tras crear el pedido con éxito
    request.session['carrito'] = {}
    request.session.modified = True

    return redirect('pedido_exitoso', pedido_id=pedido.pk), None


@login_required(login_url='login')
def pedido_exitoso(request, pedido_id):
    pedido = get_object_or_404(
        Pedido.objects.prefetch_related('items__producto'),
        pk=pedido_id,
        cliente=request.user,
    )
    return render(request, 'app_pedido/payment_success.html', {'pedido': pedido})
