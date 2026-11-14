from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Rutas de django-allauth para inicio de sesión con Google
    path('accounts/', include('allauth.urls')),

    # Rutas principales del proyecto MH'ELEGANZA
    path('', include('app_productos.urls')),
    path('carrito/', include('app_carrito.urls')),
    path('inventario/', include('app_inventario.urls')),
    
    # Rutas de pedidos y pasarela de pago (Mercado Pago)
    path('pedido/', include('app_pedido.urls')), # <--- ¡Asegúrate de tener esta línea activa!
    
    path('usuarios/', include('app_usuarios.urls')),
]

# Servir archivos multimedia (imágenes de productos, fotos de perfil) en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)