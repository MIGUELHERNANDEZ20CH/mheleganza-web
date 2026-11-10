from django.db import models
from app_productos.models import Producto

class Inventario(models.Model):
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE, related_name='inventario')
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stock de {self.producto.nombre}: {self.stock_actual} unidades"


class MovimientoInventario(models.Model):
    TIPOS = (
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('VENTA', 'Venta'),
    )

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos_inventario')
    tipo = models.CharField(max_length=10, choices=TIPOS)
    cantidad = models.PositiveIntegerField()
    stock_resultante = models.PositiveIntegerField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado_en']


class NotificacionInventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='notificaciones_inventario')
    mensaje = models.CharField(max_length=200)
    creada_en = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)

    class Meta:
        ordering = ['-creada_en']