from django.urls import path, include
from django.contrib import admin
from app_pedido.webhooks import stripe_webhook

urlpatterns = [
    path('admin/', admin.site.urls),
    path('stripe/webhook/', stripe_webhook, name='stripe_webhook'),

    # Cada app maneja sus propias rutas mediante include
    path('', include('app_productos.urls')),
    path('carrito/', include('app_carrito.urls')),
    path('inventario/', include('app_inventario.urls')),
    path('pedidos/', include('app_pedido.urls')),
    path('usuarios/', include('app_usuarios.urls')),
]