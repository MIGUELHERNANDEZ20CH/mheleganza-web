from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render

from app_productos.models import Producto, VarianteProducto
from app_productos.views import producto_para_vista


def _carrito(request):
    carrito = request.session.get('carrito', {})
    if not isinstance(carrito, dict):
        carrito = {}
    return carrito


def _guardar(request, carrito):
    request.session['carrito'] = carrito
    request.session.modified = True


def _totales(carrito):
    cantidad = sum(item['cantidad'] for item in carrito.values())
    subtotal = sum(item['precio'] * item['cantidad'] for item in carrito.values())
    for item in carrito.values():
        item['total_item'] = item['precio'] * item['cantidad']
    return cantidad, subtotal

@login_required(login_url='login')
def ver_carrito(request):
    carrito = _carrito(request)
    total_items, subtotal = _totales(carrito)
    return render(request, 'app_carrito/carrito.html', {
        'carrito': carrito,
        'total_items': total_items,
        'subtotal': subtotal,
    })

@login_required(login_url='login')
def agregar_carrito(request, producto_id):
    if request.method != 'POST':
        return redirect('catalogo')
    producto = Producto.objects.select_related('inventario').filter(
        pk=producto_id,
        disponible=True,
    ).first()
    if not producto:
        messages.error(request, 'Producto no disponible')
        return redirect(request.META.get('HTTP_REFERER', 'catalogo'))
    datos = producto_para_vista(producto)
    try:
        cantidad_solicitada = int(request.POST.get('cantidad', '1'))
    except ValueError:
        cantidad_solicitada = 0
    variante_id = request.POST.get('variante_id', '').strip()
    variante = None
    if variante_id:
        variante = VarianteProducto.objects.filter(
            pk=variante_id,
            producto=producto,
        ).first()
        if not variante:
            messages.error(request, 'Producto no disponible')
            return redirect(request.META.get('HTTP_REFERER', 'catalogo'))
    else:
        variante = VarianteProducto.objects.filter(
            producto=producto,
            talla=producto.talla,
        ).first()
    if variante:
        stock = variante.stock
        talla = variante.talla
        variante_id = str(variante.pk)
    else:
        stock = producto.inventario.stock_actual if hasattr(producto, 'inventario') else 0
        talla = producto.talla
        variante_id = ''
    if hasattr(producto, 'inventario'):
        stock = min(stock, producto.inventario.stock_actual)

    carrito = _carrito(request)
    clave = f'{producto_id}:{variante_id}' if variante_id else str(producto_id)
    cantidad_actual = carrito.get(clave, {}).get('cantidad', 0)
    nueva_cantidad = cantidad_actual + cantidad_solicitada
    if not datos['disponible'] or cantidad_solicitada < 1 or nueva_cantidad > stock:
        messages.error(request, 'Producto no disponible')
        return redirect(request.META.get('HTTP_REFERER', 'catalogo'))
    carrito[clave] = {
        'producto_id': producto_id,
        'variante_id': variante_id,
        'talla': talla,
        'nombre': datos['nombre'],
        'precio': float(datos['precio']),
        'imagen_url': datos['imagen_url'],
        'cantidad': nueva_cantidad,
    }
    _guardar(request, carrito)
    messages.success(request, 'Producto agregado al carrito.')
    return redirect('ver_carrito')

@login_required(login_url='login')
def eliminar_carrito_item(request, item_id):
    if request.method != 'POST':
        return redirect('ver_carrito')
    carrito = _carrito(request)
    carrito.pop(str(item_id), None)
    _guardar(request, carrito)
    return redirect('ver_carrito')

@login_required(login_url='login')
def actualizar_cantidad(request, item_id):
    if request.method == 'POST':
        carrito = _carrito(request)
        clave = str(item_id)
        try:
            cantidad = int(request.POST.get('cantidad', '0'))
        except ValueError:
            cantidad = 0
        if clave in carrito and cantidad > 0:
            item = carrito[clave]
            producto = Producto.objects.filter(
                pk=item.get('producto_id'),
                disponible=True,
            ).select_related('inventario').first()
            variante = VarianteProducto.objects.filter(
                pk=item.get('variante_id'),
                producto=producto,
            ).first() if producto and item.get('variante_id') else None
            stock = (
                variante.stock if variante else
                producto.inventario.stock_actual if producto and hasattr(producto, 'inventario') else 0
            )
            if producto and variante and hasattr(producto, 'inventario'):
                stock = min(stock, producto.inventario.stock_actual)
            if producto and cantidad <= stock:
                carrito[clave]['cantidad'] = cantidad
                _guardar(request, carrito)
            else:
                messages.error(request, 'Producto no disponible')
        else:
            messages.error(request, 'La cantidad debe ser mayor que cero.')
    return redirect('ver_carrito')

@login_required(login_url='login')
def vaciar_carrito(request):
    if request.method != 'POST':
        return redirect('ver_carrito')
    _guardar(request, {})
    return redirect('ver_carrito')

@login_required(login_url='login')
def calcular_total_carrito(request):
    return ver_carrito(request)