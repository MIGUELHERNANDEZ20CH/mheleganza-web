from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalogo_view, name='catalogo'),
    path('producto/<int:producto_id>/', views.detalle_producto_view, name='detalle_producto'),
    path('favorito/quitar/<int:producto_id>/', views.quitar_favorito_view, name='quitar_favorito'),
    path('favoritos/', views.ver_favoritos_view, name='ver_favoritos'),
    path('admin-productos/', views.admin_productos_view, name='admin_productos'),
    path('admin-productos/eliminar/<int:producto_id>/', views.admin_eliminar_producto_view, name='admin_eliminar_producto'),
]