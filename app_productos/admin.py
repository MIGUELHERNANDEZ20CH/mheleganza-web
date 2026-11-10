from django.contrib import admin

from .models import ImagenProducto, Producto, VarianteProducto


class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    extra = 1


class VarianteProductoInline(admin.TabularInline):
    model = VarianteProducto
    extra = 1


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'categoria', 'precio', 'disponible')
    search_fields = ('nombre', 'marca')
    list_filter = ('marca', 'categoria', 'disponible')
    inlines = (ImagenProductoInline, VarianteProductoInline)
