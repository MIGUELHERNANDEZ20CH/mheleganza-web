from django.urls import path
from . import views

urlpatterns = [
    path('', views.ver_carrito, name='ver_carrito'),
    path('agregar/<int:producto_id>/', views.agregar_carrito, name='agregar_carrito'),
    path('eliminar/<str:item_id>/', views.eliminar_carrito_item, name='eliminar_carrito_item'),
    path('actualizar/<str:item_id>/', views.actualizar_cantidad, name='actualizar_cantidad'),
    path('vaciar/', views.vaciar_carrito, name='vaciar_carrito'),
    path('total/', views.calcular_total_carrito, name='calcular_total_carrito'),
]