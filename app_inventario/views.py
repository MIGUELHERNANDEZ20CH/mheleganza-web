from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .models import Inventario, MovimientoInventario, NotificacionInventario
from app_productos.models import Producto, VarianteProducto


def _es_admin(request):
    usuario = request.session.get('usuario')
    return bool(usuario and usuario.get('rol') == 'admin')


def _render_panel_inventario(request, inventarios, agotados, stock_bajo, movimientos):
    return render(request, 'app_inventario/admin_panel.html', {
        'inventarios': inventarios,
        'agotados': agotados,
        'stock_bajo': stock_bajo,
        'notificaciones': NotificacionInventario.objects.select_related('producto').filter(leida=False),
        'movimientos': movimientos,
    })


def panel_inventario(request):
    if not _es_admin(request):
        return redirect('login')
    inventarios = Inventario.objects.select_related('producto').order_by('producto__nombre')
    return _render_panel_inventario(
        request,
        inventarios,
        inventarios.filter(stock_actual=0),
        inventarios.filter(stock_actual__gt=0, stock_actual__lte=5),
        MovimientoInventario.objects.select_related('producto')[:20],
    )


def _ajustar_stock(request, cantidad_campo, entrada):
    if not _es_admin(request):
        return redirect('login')
    if request.method != 'POST':
        return redirect('panel_inventario')
    try:
        producto_id = int(request.POST.get('producto_id', '0'))
        cantidad = int(request.POST.get(cantidad_campo, '0'))
        if cantidad <= 0:
            raise ValueError
        with transaction.atomic():
            producto = get_object_or_404(Producto.objects.select_for_update(), pk=producto_id)
            inventario = Inventario.objects.select_for_update().get(producto=producto)
            variante_id = request.POST.get('variante_id', '').strip()
            variantes = VarianteProducto.objects.select_for_update().filter(producto=producto)
            if variante_id:
                variante = variantes.filter(pk=variante_id).first()
                if not variante:
                    messages.error(request, 'Selecciona una talla válida para actualizar el inventario.')
                    return redirect('panel_inventario')
                nuevo_stock_variante = variante.stock + cantidad if entrada else variante.stock - cantidad
                if nuevo_stock_variante < 0:
                    messages.error(request, 'Stock insuficiente para registrar la salida de esta talla.')
                    return redirect('panel_inventario')
                variante.stock = nuevo_stock_variante
                variante.save(update_fields=['stock'])
                nuevo_stock = sum(variantes.values_list('stock', flat=True))
            elif variantes.exists():
                variante = variantes.filter(talla=producto.talla).first() or variantes.first()
                nuevo_stock_variante = variante.stock + cantidad if entrada else variante.stock - cantidad
                if nuevo_stock_variante < 0:
                    messages.error(request, 'Stock insuficiente para registrar la salida.')
                    return redirect('panel_inventario')
                variante.stock = nuevo_stock_variante
                variante.save(update_fields=['stock'])
                nuevo_stock = sum(variantes.values_list('stock', flat=True))
            else:
                nuevo_stock = inventario.stock_actual + cantidad if entrada else inventario.stock_actual - cantidad
                if nuevo_stock < 0:
                    messages.error(request, 'Stock insuficiente para registrar la salida.')
                    return redirect('panel_inventario')
            inventario.stock_actual = nuevo_stock
            inventario.save(update_fields=['stock_actual', 'actualizado_en'])
            MovimientoInventario.objects.create(
                producto=producto,
                tipo='ENTRADA' if entrada else 'SALIDA',
                cantidad=cantidad,
                stock_resultante=nuevo_stock,
            )
            producto.disponible = nuevo_stock > 0
            producto.save(update_fields=['disponible'])
            if nuevo_stock == 0:
                NotificacionInventario.objects.create(
                    producto=producto,
                    mensaje=f'{producto.nombre} se quedó sin unidades disponibles.',
                )
        messages.success(request, 'Actualización exitosa')
    except (ValueError, Inventario.DoesNotExist):
        messages.error(request, 'Ingresa una cantidad válida y verifica el inventario del producto.')
    return redirect('panel_inventario')


def registrar_entrada(request):
    return _ajustar_stock(request, 'cantidad_entrada', True)


def registrar_salida(request):
    return _ajustar_stock(request, 'cantidad_salida', False)


def alerta_stock_bajo(request):
    if not _es_admin(request):
        return redirect('login')
    inventarios_bajos = Inventario.objects.select_related('producto').filter(
        stock_actual__lte=5,
    ).order_by('stock_actual')
    inventarios = Inventario.objects.select_related('producto').all()
    return _render_panel_inventario(
        request,
        inventarios,
        inventarios_bajos.filter(stock_actual=0),
        inventarios_bajos.filter(stock_actual__gt=0),
        MovimientoInventario.objects.select_related('producto')[:20],
    )


def historial_movimientos(request):
    if not _es_admin(request):
        return redirect('login')
    inventarios = Inventario.objects.select_related('producto')
    return _render_panel_inventario(
        request,
        inventarios,
        inventarios.filter(stock_actual=0),
        inventarios.filter(stock_actual__gt=0, stock_actual__lte=5),
        MovimientoInventario.objects.select_related('producto').all(),
    )


def reporte_inventario(request):
    return panel_inventario(request)