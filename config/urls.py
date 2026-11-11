from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app_pedido.webhooks import stripe_webhook

urlpatterns = [
    path('admin/', admin.site.urls),
    path('stripe/webhook/', stripe_webhook, name='stripe_webhook'),

    # Rutas de django-allauth para inicio de sesión con Google
    path('accounts/', include('allauth.urls')),

    # Rutas principales del proyecto
    path('', include('app_productos.urls')),
    path('carrito/', include('app_carrito.urls')),
    path('inventario/', include('app_inventario.urls')),
    path('pedidos/', include('app_pedido.urls')),
    path('usuarios/', include('app_usuarios.urls')),
]

# Servir archivos multimedia (imágenes de productos, fotos de perfil) en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)