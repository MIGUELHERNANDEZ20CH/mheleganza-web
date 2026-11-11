import logging
from decimal import Decimal

from django.contrib import messages
from django.conf import settings
from django.db import DatabaseError, transaction
from django.shortcuts import get_object_or_404, redirect, render

from app_inventario.models import Inventario, MovimientoInventario, NotificacionInventario
from app_productos.models import Producto, VarianteProducto
from .models import DetallePedido, Pedido
from .notifications import (
    enviar_alerta_nuevo_pedido,
    enviar_aviso_cambio_estado_pedido,
)
from .services import enviar_confirmacion_pedido

logger = logging.getLogger(__name__)


class PagoRechazado(Exception):
    pass


def procesar_pago_simulado(metodo_pago):
    return settings.DEBUG and metodo_pago in dict(Pedido.METODOS_PAGO)


def _carrito(request):
    carrito = request.session.get('carrito', {})
    return carrito if isinstance(carrito, dict) else {}


def _resumen(carrito):
    total_items = sum(item.get('cantidad', 0) for item in carrito.values())
    subtotal = sum(Decimal(str(item['precio'])) * item['cantidad'] for item in carrito.values())
    return total_items, subtotal


def resumen_pedido_carrito(request):
    return redirect('ver_carrito')


def checkout_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    carrito = _carrito(request)
    if not carrito:
        messages.error(request, 'Tu carrito está vacío.')
        return redirect('ver_carrito')

    error_pago = None
    error_direccion = False
    error_metodo_pago = False
    if request.method == 'POST':
        direccion = request.POST.get('direccion', '').strip()
        metodo_pago = request.POST.get('metodo_pago', '')
        valid_methods = dict(Pedido.METODOS_PAGO)
        error_direccion = not direccion
        error_metodo_pago = metodo_pago not in valid_methods
        if error_direccion or error_metodo_pago:
            error_pago = 'Completa la dirección y selecciona un medio de pago válido.'
        elif metodo_pago == 'TARJETA':
            from .views_checkout import crear_checkout_stripe

            stripe_redirect, stripe_error = crear_checkout_stripe(request, direccion)
            if stripe_redirect:
                return stripe_redirect
            error_pago = stripe_error
        else:
            try:
                with transaction.atomic():
                    lineas = []
                    total = Decimal('0.00')
                    reservas_producto = {}
                    reservas_variante = {}
                    for item in carrito.values():
                        producto = Producto.objects.select_for_update().get(pk=item['producto_id'], disponible=True)
                        inventario = Inventario.objects.select_for_update().get(producto=producto)
                        variante_id = item.get('variante_id')
                        if variante_id:
                            variante = VarianteProducto.objects.select_for_update().filter(
                                pk=variante_id,
                                producto=producto,
                            ).first()
                        else:
                            variante = VarianteProducto.objects.select_for_update().filter(
                                producto=producto,
                                talla=item.get('talla') or producto.talla,
                            ).first()
                        cantidad = int(item['cantidad'])
                        stock_producto_reservado = reservas_producto.get(producto.pk, 0)
                        stock_variante_reservado = reservas_variante.get(variante.pk, 0) if variante else 0
                        if (
                            cantidad < 1
                            or inventario.stock_actual - stock_producto_reservado < cantidad
                            or (
                                variante
                                and variante.stock - stock_variante_reservado < cantidad
                            )
                            or (variante_id and not variante)
                        ):
                            raise ValueError('Producto no disponible.')
                        reservas_producto[producto.pk] = stock_producto_reservado + cantidad
                        if variante:
                            reservas_variante[variante.pk] = stock_variante_reservado + cantidad
                        precio = producto.precio
                        lineas.append((producto, inventario, variante, cantidad, precio))
                        total += precio * cantidad

                    if not procesar_pago_simulado(metodo_pago):
                        raise PagoRechazado

                    pedido = Pedido.objects.create(
                        cliente=request.user,
                        metodo_pago=metodo_pago,
                        total=total,
                        direccion_envio=direccion,
                        estado='PAGADO',
                    )
                    inventarios_actualizados = {}
                    variantes_actualizadas = {}
                    for producto, inventario, variante, cantidad, precio in lineas:
                        DetallePedido.objects.create(
                            pedido=pedido,
                            producto=producto,
                            talla=variante.talla if variante else producto.talla,
                            cantidad=cantidad,
                            precio_unitario=precio,
                        )
                        if variante:
                            variante_guardada = variantes_actualizadas.get(variante.pk, variante)
                            variante_guardada.stock -= cantidad
                            variante_guardada.save(update_fields=['stock'])
                            variantes_actualizadas[variante.pk] = variante_guardada
                        inventario_guardado = inventarios_actualizados.get(producto.pk, inventario)
                        inventario_guardado.stock_actual -= cantidad
                        inventario_guardado.save(update_fields=['stock_actual', 'actualizado_en'])
                        inventarios_actualizados[producto.pk] = inventario_guardado
                        MovimientoInventario.objects.create(
                            producto=producto,
                            tipo='VENTA',
                            cantidad=cantidad,
                            stock_resultante=inventario_guardado.stock_actual,
                        )
                        if inventario_guardado.stock_actual == 0:
                            producto.disponible = False
                            producto.save(update_fields=['disponible'])
                            NotificacionInventario.objects.create(
                                producto=producto,
                                mensaje=f'{producto.nombre} se quedó sin unidades disponibles.',
                            )
            except PagoRechazado:
                error_pago = 'Pago rechazado'
            except (Producto.DoesNotExist, Inventario.DoesNotExist, ValueError):
                error_pago = 'Producto no disponible'
            else:
                request.session['carrito'] = {}
                enviar_alerta_nuevo_pedido(pedido.pk)
                email_enviado = 0
                if request.user.email:
                    try:
                        email_enviado = enviar_confirmacion_pedido(pedido.pk)
                    except (OSError, ValueError, RuntimeError):
                        logger.exception('Could not send order confirmation')
                mensaje = f'Pedido #{pedido.pk} generado. Estado: {pedido.get_estado_display}.'
                if email_enviado:
                    mensaje += ' Confirmación enviada a tu correo.'
                messages.success(request, mensaje)
                return redirect('mis_pedidos')

    total_items, subtotal = _resumen(carrito)
    lineas_carrito = [
        {
            **item,
            'subtotal': Decimal(str(item['precio'])) * item['cantidad'],
        }
        for item in carrito.values()
    ]
    return render(request, 'app_pedido/checkout.html', {
        'carrito': carrito,
        'lineas_carrito': lineas_carrito,
        'subtotal': subtotal,
        'total_items': total_items,
        'error_pago': error_pago,
        'error_direccion': error_direccion,
        'error_metodo_pago': error_metodo_pago,
        'direccion_actual': request.POST.get('direccion', request.session.get('direccion_usuario', '')),
        'metodo_pago_actual': request.POST.get('metodo_pago', ''),
    })


def mis_pedidos_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    pedidos = Pedido.objects.filter(cliente=request.user).prefetch_related('items__producto').order_by('-fecha_creacion')
    carrito = _carrito(request)
    total_items, _ = _resumen(carrito)
    return render(request, 'app_pedido/mis_pedidos.html', {'pedidos': pedidos, 'total_items': total_items})


def detalle_pedido_view(request, pedido_id):
    if not request.user.is_authenticated:
        return redirect('login')
    pedido_query = Pedido.objects.prefetch_related('items__producto')
    try:
        if request.user.is_staff:
            pedido = get_object_or_404(pedido_query, pk=pedido_id)
        else:
            pedido = get_object_or_404(pedido_query, pk=pedido_id, cliente=request.user)
    except DatabaseError:
        messages.error(request, 'Error al cargar pedido')
        return redirect('admin_productos' if request.user.is_staff else 'mis_pedidos')
    return render(request, 'app_pedido/mis_pedidos.html', {
        'pedido_seleccionado': pedido,
        'pedidos': [pedido],
        'es_admin': request.user.is_staff,
    })


def cancelar_pedido_view(request, pedido_id):
    if not request.user.is_authenticated:
        return redirect('login')
    pedido = get_object_or_404(Pedido, pk=pedido_id, cliente=request.user)
    if request.method == 'POST' and pedido.estado == 'PENDIENTE':
        pedido.estado = 'RECHAZADO'
        pedido.save(update_fields=['estado'])
    return redirect('mis_pedidos')


def actualizar_estado_pedido(request, pedido_id):
    usuario = request.session.get('usuario')
    if not usuario or usuario.get('rol') != 'admin':
        return redirect('login')
    if request.method != 'POST':
        return redirect('admin_productos')

    estado = request.POST.get('nuevo_estado', '')
    transiciones = {
        'PENDIENTE': {'PAGADO'},
        'PAGADO': {'ENVIADO'},
        'ENVIADO': {'ENTREGADO'},
        'ENTREGADO': set(),
        'RECHAZADO': set(),
    }
    with transaction.atomic():
        pedido = get_object_or_404(
            Pedido.objects.select_for_update(),
            pk=pedido_id,
        )
        estado_anterior = pedido.estado
        if estado not in dict(Pedido.ESTADOS) or estado not in transiciones[estado_anterior]:
            messages.error(request, 'Cambio de estado no permitido.')
        elif estado != estado_anterior:
            pedido.estado = estado
            pedido.save(update_fields=['estado'])
            transaction.on_commit(
                lambda pedido_id=pedido.pk, anterior=estado_anterior, nuevo=estado: (
                    enviar_aviso_cambio_estado_pedido(pedido_id, anterior, nuevo)
                )
            )
            messages.success(request, 'Estado del pedido actualizado.')
    return redirect('admin_productos')