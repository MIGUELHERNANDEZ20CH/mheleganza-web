from django.urls import path
from . import views

urlpatterns = [
    path('resumen/', views.resumen_pedido_carrito, name='resumen_pedido_carrito'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('mis-pedidos/', views.mis_pedidos_view, name='mis_pedidos'),
    path('detalle/<int:pedido_id>/', views.detalle_pedido_view, name='detalle_pedido'),
    path('cancelar/<int:pedido_id>/', views.cancelar_pedido_view, name='cancelar_pedido'),
    path('actualizar/<int:pedido_id>/', views.actualizar_estado_pedido, name='actualizar_estado_pedido'),
]