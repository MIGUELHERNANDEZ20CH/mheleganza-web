from django.urls import path
from . import views

urlpatterns = [
    path('', views.panel_inventario, name='panel_inventario'),
    path('entrada/', views.registrar_entrada, name='registrar_entrada'),
    path('salida/', views.registrar_salida, name='registrar_salida'),
    path('alertas/', views.alerta_stock_bajo, name='alerta_stock_bajo'),
    path('historial/', views.historial_movimientos, name='historial_movimientos'),
    path('reporte/', views.reporte_inventario, name='reporte_inventario'),
]