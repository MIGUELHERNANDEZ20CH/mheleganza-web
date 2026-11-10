from django.db import models
from django.contrib.auth.models import User
from app_productos.models import Producto

class Pedido(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('ENVIADO', 'Enviado'),
        ('ENTREGADO', 'Entregado'),
        ('RECHAZADO', 'Pago Rechazado'),
    ]

    METODOS_PAGO = [
        ('TARJETA', 'Tarjeta de Crédito/Débito'),
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
        ('CONTRAENTREGA', 'Pago Contraentrega'),
    ]

    cliente = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    metodo_pago = models.CharField(max_length=30, choices=METODOS_PAGO)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    direccion_envio = models.TextField()
    stripe_checkout_session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    confirmacion_email_enviada = models.BooleanField(default=False)

    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.username} [{self.estado}]"

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    talla = models.CharField(max_length=20, blank=True)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def __str__(self):
        return f"{self.cantidad} de {self.producto.nombre} en Pedido #{self.pedido.id}"