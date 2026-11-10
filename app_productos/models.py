from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=100)
    talla = models.CharField(max_length=20)  # S, M, L, XL, etc.
    color = models.CharField(max_length=50)
    marca = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    imagen_url = models.URLField(blank=True)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.talla} - {self.color})"


class ImagenProducto(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='galeria',
    )
    imagen = models.ImageField(upload_to='productos/galeria/', blank=True, null=True)
    imagen_url = models.URLField(blank=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('orden', 'pk')

    def __str__(self):
        return f"Imagen de {self.producto.nombre}"


class VarianteProducto(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='variantes',
    )
    talla = models.CharField(max_length=20)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('talla',)
        constraints = [
            models.UniqueConstraint(
                fields=('producto', 'talla'),
                name='unique_talla_por_producto',
            ),
        ]

    def __str__(self):
        return f"{self.producto.nombre} - {self.talla} ({self.stock})"