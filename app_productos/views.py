from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie

from app_inventario.models import Inventario, NotificacionInventario
from app_pedido.models import Pedido
from .models import ImagenProducto, Producto, VarianteProducto


def producto_para_vista(producto):
    inventario = getattr(producto, 'inventario', None)
    variantes = list(producto.variantes.all())
    if not variantes:
        tallas_disponibles = [{
            'id': '',
            'talla': producto.talla,
            'stock': inventario.stock_actual if inventario else 0,
        }]
    else:
        tallas_disponibles = [
            {'id': variante.pk, 'talla': variante.talla, 'stock': variante.stock}
            for variante in variantes
            if variante.stock > 0
        ]
    variantes_para_vista = [
        {'id': variante.pk, 'talla': variante.talla, 'stock': variante.stock}
        for variante in variantes
    ]
    stock = sum(talla['stock'] for talla in tallas_disponibles)
    if inventario:
        stock = min(stock, inventario.stock_actual)

    imagenes = [
        {
            'url': imagen.imagen_url or (imagen.imagen.url if imagen.imagen else ''),
            'alt': producto.nombre,
        }
        for imagen in producto.galeria.all()
        if imagen.imagen_url or imagen.imagen
    ]
    imagen_principal = producto.imagen_url or (producto.imagen.url if producto.imagen else '')
    if not imagenes and imagen_principal:
        imagenes = [{'url': imagen_principal, 'alt': producto.nombre}]

    return {
        'id': producto.pk,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'precio': producto.precio,
        'categoria': producto.categoria,
        'talla': producto.talla,
        'color': producto.color,
        'marca': producto.marca,
        'imagen_url': imagen_principal,
        'imagenes': imagenes,
        'tallas_disponibles': tallas_disponibles,
        'variantes': variantes_para_vista,
        'disponible': producto.disponible and stock > 0 and bool(tallas_disponibles),
        'stock': stock,
    }


@ensure_csrf_cookie
@never_cache
def catalogo_view(request):
    filtros = {
        'categoria': request.GET.get('categoria', '').strip(),
        'talla': request.GET.get('talla', '').strip(),
        'color': request.GET.get('color', '').strip(),
        'marca': request.GET.get('marca', '').strip(),
        'precio_min': request.GET.get('precio_min', '').strip(),
        'precio_max': request.GET.get('precio_max', '').strip(),
    }
    try:
        disponibles = Producto.objects.filter(
            disponible=True,
            inventario__stock_actual__gt=0,
        ).select_related('inventario').prefetch_related('variantes', 'galeria')
        consulta = disponibles
        opciones_filtro = {
            campo: list(
                disponibles
                .order_by(campo)
                .values_list(campo, flat=True)
                .distinct()
            )
            for campo in ('categoria', 'talla', 'color', 'marca')
        }
        for campo in ('categoria', 'talla', 'color', 'marca'):
            if filtros[campo]:
                consulta = consulta.filter(**{f'{campo}__icontains': filtros[campo]})
        for campo, operador in (('precio_min', 'gte'), ('precio_max', 'lte')):
            if filtros[campo]:
                try:
                    valor = Decimal(filtros[campo])
                    if not valor.is_finite() or valor < 0:
                        raise InvalidOperation
                    consulta = consulta.filter(**{f'precio__{operador}': valor})
                except InvalidOperation:
                    nombre_filtro = 'precio mínimo' if campo == 'precio_min' else 'precio máximo'
                    messages.error(request, f'El {nombre_filtro} debe ser un número válido mayor o igual a cero.')
                    filtros[campo] = ''
        productos = [producto_para_vista(producto) for producto in consulta]
        novedades = []
        imagenes_novedades = set()
        for producto in disponibles.order_by('-pk'):
            destacado = producto_para_vista(producto)
            if destacado['imagen_url'] and destacado['imagen_url'] not in imagenes_novedades:
                novedades.append(destacado)
                imagenes_novedades.add(destacado['imagen_url'])
                if len(novedades) == 4:
                    break
    except DatabaseError:
        messages.error(request, 'Error al cargar el catálogo. Inténtalo nuevamente.')
        productos = []
        novedades = []
        opciones_filtro = {campo: [] for campo in ('categoria', 'talla', 'color', 'marca')}

    carrito = request.session.get('carrito', {})
    total_items = sum(item.get('cantidad', 0) for item in carrito.values()) if isinstance(carrito, dict) else 0
    return render(request, 'app_productos/catalogo.html', {
        'productos': productos,
        'categoria_actual': filtros['categoria'],
        'talla_actual': filtros['talla'],
        'color_actual': filtros['color'],
        'marca_actual': filtros['marca'],
        'opciones_filtro': opciones_filtro,
        'precio_min_actual': filtros['precio_min'],
        'precio_max_actual': filtros['precio_max'],
        'hay_filtros': any(filtros.values()),
        'novedades': novedades,
        'marcas_disponibles': opciones_filtro['marca'],
        'total_items': total_items,
    })


def detalle_producto_view(request, producto_id):
    producto = Producto.objects.filter(
        pk=producto_id,
        disponible=True,
        inventario__stock_actual__gt=0,
    ).select_related('inventario').prefetch_related('variantes', 'galeria').first()
    datos_producto = producto_para_vista(producto) if producto else None
    carrito = request.session.get('carrito', {})
    total_items = sum(item.get('cantidad', 0) for item in carrito.values()) if isinstance(carrito, dict) else 0
    return render(request, 'app_productos/detalle_producto.html', {
        'producto': datos_producto,
        'tallas_disponibles': datos_producto['tallas_disponibles'] if datos_producto else [],
        'total_items': total_items,
        'favoritos': request.session.get('favoritos', []),
    })


def quitar_favorito_view(request, producto_id):
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER', 'catalogo'))
    if not Producto.objects.filter(pk=producto_id).exists():
        messages.error(request, 'Producto no disponible')
        return redirect('catalogo')
    favoritos = request.session.get('favoritos', [])
    if producto_id in favoritos:
        favoritos.remove(producto_id)
    request.session['favoritos'] = favoritos
    return redirect(request.META.get('HTTP_REFERER', 'catalogo'))


def ver_favoritos_view(request):
    ids = request.session.get('favoritos', [])
    productos = [
        producto_para_vista(p)
        for p in Producto.objects.filter(pk__in=ids)
        .select_related('inventario')
        .prefetch_related('variantes', 'galeria')
    ]
    carrito = request.session.get('carrito', {})
    total_items = sum(item.get('cantidad', 0) for item in carrito.values()) if isinstance(carrito, dict) else 0
    return render(request, 'app_productos/favoritos.html', {'productos': productos, 'total_items': total_items})


def admin_productos_view(request):
    usuario = request.session.get('usuario')
    if not usuario or usuario.get('rol') != 'admin':
        return redirect('login')

    if request.method == 'POST' and 'agregar_producto' in request.POST:
        try:
            with transaction.atomic():
                stock = int(request.POST.get('stock', '0'))
                if stock < 0:
                    raise ValueError
                precio = Decimal(request.POST.get('precio', '0'))
                if not precio.is_finite() or precio < 0:
                    raise ValueError
                producto = Producto(
                    nombre=request.POST.get('nombre', '').strip(),
                    descripcion=request.POST.get('descripcion', '').strip(),
                    precio=precio,
                    categoria=request.POST.get('categoria', '').strip(),
                    talla=request.POST.get('talla', '').strip(),
                    color=request.POST.get('color', '').strip(),
                    marca=request.POST.get('marca', '').strip(),
                    imagen_url=request.POST.get('imagen_url', '').strip(),
                    disponible=stock > 0,
                )
                producto.full_clean()
                producto.save()
                Inventario.objects.create(producto=producto, stock_actual=stock)
                VarianteProducto.objects.create(
                    producto=producto,
                    talla=producto.talla,
                    stock=stock,
                )
                if producto.imagen_url:
                    ImagenProducto.objects.create(
                        producto=producto,
                        imagen_url=producto.imagen_url,
                    )
                if stock == 0:
                    NotificacionInventario.objects.create(
                        producto=producto,
                        mensaje=f'{producto.nombre} se quedó sin unidades disponibles.',
                    )
            messages.success(request, 'Producto registrado')
        except (ValueError, InvalidOperation, IntegrityError, ValidationError):
            messages.error(request, 'No se pudo registrar el producto. Verifica los datos ingresados.')
        return redirect('admin_productos')

    if request.method == 'POST' and 'actualizar_stock' in request.POST:
        try:
            producto_id = int(request.POST.get('producto_id', '0'))
            stock = int(request.POST.get('stock', '-1'))
            if stock < 0:
                raise ValueError
            with transaction.atomic():
                producto = get_object_or_404(
                    Producto.objects.select_for_update(),
                    pk=producto_id,
                )
                inventario, creado = (
                    Inventario.objects.select_for_update().get_or_create(
                        producto=producto,
                        defaults={'stock_actual': 0},
                    )
                )
                variantes = VarianteProducto.objects.select_for_update().filter(
                    producto=producto,
                )
                variante_id = request.POST.get('variante_id', '').strip()
                if variante_id:
                    variante = variantes.filter(pk=variante_id).first()
                    if not variante:
                        raise ValueError
                    variante.stock = stock
                    variante.save(update_fields=['stock'])
                    stock = sum(variantes.values_list('stock', flat=True))
                elif variantes.exists():
                    raise ValueError
                stock_anterior = inventario.stock_actual
                if inventario.stock_actual != stock:
                    inventario.stock_actual = stock
                    inventario.save(update_fields=['stock_actual', 'actualizado_en'])
                if stock == 0 and (creado or stock_anterior > 0):
                    NotificacionInventario.objects.create(
                        producto=producto,
                        mensaje=f'{producto.nombre} se quedó sin unidades disponibles.',
                    )
                producto.disponible = stock > 0
                producto.save(update_fields=['disponible'])
            messages.success(request, 'Actualización exitosa')
        except ValueError:
            messages.error(request, 'El stock debe ser un número igual o mayor que cero.')
        return redirect('admin_productos')

    productos = [
        producto_para_vista(p)
        for p in Producto.objects.select_related('inventario').prefetch_related('variantes', 'galeria')
    ]
    stock_agotado = Producto.objects.filter(inventario__stock_actual=0).values_list('nombre', flat=True)
    fecha = request.GET.get('fecha', '').strip()
    estado = request.GET.get('estado', '').strip()
    cliente = request.GET.get('cliente', '').strip()
    try:
        pedidos = Pedido.objects.select_related('cliente').prefetch_related('items__producto').order_by('-fecha_creacion')
        if fecha:
            pedidos = pedidos.filter(fecha_creacion__date=fecha)
        if estado in dict(Pedido.ESTADOS):
            pedidos = pedidos.filter(estado=estado)
        if cliente:
            pedidos = pedidos.filter(Q(cliente__username__icontains=cliente) | Q(cliente__email__icontains=cliente) | Q(cliente__first_name__icontains=cliente))
        pedidos = list(pedidos)
    except DatabaseError:
        pedidos = []
        error_pedidos = True
    else:
        error_pedidos = False
    carrito = request.session.get('carrito', {})
    total_items = sum(item.get('cantidad', 0) for item in carrito.values()) if isinstance(carrito, dict) else 0
    return render(request, 'app_productos/admin_productos.html', {
        'productos': productos,
        'pedidos': pedidos,
        'error_pedidos': error_pedidos,
        'estados_pedido': Pedido.ESTADOS,
        'filtros_pedidos': {'fecha': fecha, 'estado': estado, 'cliente': cliente},
        'stock_agotado': stock_agotado,
        'total_items': total_items,
    })


def admin_eliminar_producto_view(request, producto_id):
    usuario = request.session.get('usuario')
    if not usuario or usuario.get('rol') != 'admin':
        return redirect('login')
    if request.method != 'POST':
        return redirect('admin_productos')
    Producto.objects.filter(pk=producto_id).delete()
    messages.success(request, 'Producto eliminado.')
    return redirect('admin_productos')