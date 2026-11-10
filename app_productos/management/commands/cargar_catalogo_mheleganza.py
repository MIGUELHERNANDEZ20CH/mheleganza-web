from django.core.management.base import BaseCommand
from django.db import transaction

from app_inventario.models import Inventario
from app_productos.models import ImagenProducto, Producto, VarianteProducto


PRODUCTOS = [
    {
        'nombre': 'Polo de piqué con logo Psycho Bunny',
        'marca': 'Psycho Bunny',
        'categoria': 'Polos',
        'descripcion': 'Polo de algodón piqué con cuello clásico y detalle gráfico en el pecho.',
        'precio': '429000.00',
        'talla': 'M',
        'color': 'Negro',
        'stock': 8,
        'imagen_url': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Camiseta gráfica Psycho Bunny',
        'marca': 'Psycho Bunny',
        'categoria': 'Camisetas',
        'descripcion': 'Camiseta casual de algodón de manga corta con estampado frontal.',
        'precio': '289000.00',
        'talla': 'L',
        'color': 'Blanco',
        'stock': 10,
        'imagen_url': 'https://images.unsplash.com/photo-1576566588028-4147f3842f27?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Hoodie con logo Psycho Bunny',
        'marca': 'Psycho Bunny',
        'categoria': 'Hoodies',
        'descripcion': 'Buzo con capucha, bolsillo canguro y acabado suave para uso diario.',
        'precio': '689000.00',
        'talla': 'XL',
        'color': 'Gris',
        'stock': 5,
        'imagen_url': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Polo clásico petit piqué Lacoste',
        'marca': 'Lacoste',
        'categoria': 'Polos',
        'descripcion': 'Polo de manga corta en tejido piqué con cuello acanalado y tapeta de botones.',
        'precio': '499000.00',
        'talla': 'M',
        'color': 'Verde',
        'stock': 9,
        'imagen_url': 'https://images.unsplash.com/photo-1598033129183-c4f50c736f10?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Camisa Oxford Lacoste',
        'marca': 'Lacoste',
        'categoria': 'Camisas',
        'descripcion': 'Camisa de algodón tipo Oxford con cuello abotonado y puños clásicos.',
        'precio': '579000.00',
        'talla': 'L',
        'color': 'Celeste',
        'stock': 6,
        'imagen_url': 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Tenis Lacoste Carnaby Pro',
        'marca': 'Lacoste',
        'categoria': 'Calzado',
        'descripcion': 'Tenis de inspiración clásica con exterior de acabado limpio y suela de goma.',
        'precio': '649000.00',
        'talla': '40',
        'color': 'Blanco',
        'stock': 4,
        'imagen_url': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Hoodie con bandera Tommy Hilfiger',
        'marca': 'Tommy Hilfiger',
        'categoria': 'Hoodies',
        'descripcion': 'Buzo de algodón con capucha, bolsillo frontal y detalle de bandera.',
        'precio': '559000.00',
        'talla': 'M',
        'color': 'Azul marino',
        'stock': 7,
        'imagen_url': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Camisa stretch Tommy Hilfiger',
        'marca': 'Tommy Hilfiger',
        'categoria': 'Camisas',
        'descripcion': 'Camisa de corte moderno con cuello clásico y tejido ligero con elasticidad.',
        'precio': '499000.00',
        'talla': 'L',
        'color': 'Blanco',
        'stock': 6,
        'imagen_url': 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Gorra clásica Tommy Hilfiger',
        'marca': 'Tommy Hilfiger',
        'categoria': 'Accesorios',
        'descripcion': 'Gorra de seis paneles con visera curva y correa posterior ajustable.',
        'precio': '229000.00',
        'talla': 'Única',
        'color': 'Azul marino',
        'stock': 12,
        'imagen_url': 'https://images.unsplash.com/photo-1588850561407-ed78c282e89b?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Camiseta UA Tech 2.0',
        'marca': 'Under Armour',
        'categoria': 'Camisetas deportivas',
        'descripcion': 'Camiseta deportiva ligera de secado rápido para entrenamiento y actividad diaria.',
        'precio': '189000.00',
        'talla': 'M',
        'color': 'Negro',
        'stock': 14,
        'imagen_url': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Tenis de running UA Charged Assert',
        'marca': 'Under Armour',
        'categoria': 'Calzado',
        'descripcion': 'Tenis de running con parte superior transpirable y suela acolchada.',
        'precio': '429000.00',
        'talla': '41',
        'color': 'Negro y blanco',
        'stock': 5,
        'imagen_url': 'https://images.unsplash.com/photo-1600185365483-26d7a4cc7519?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Camiseta Ikonik Karl Lagerfeld',
        'marca': 'Karl Lagerfeld',
        'categoria': 'Camisetas',
        'descripcion': 'Camiseta de algodón de manga corta con gráfico frontal de inspiración Ikonik.',
        'precio': '399000.00',
        'talla': 'M',
        'color': 'Negro',
        'stock': 6,
        'imagen_url': 'https://images.unsplash.com/photo-1576566588028-4147f3842f27?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Bolso crossbody K/Essential Karl Lagerfeld',
        'marca': 'Karl Lagerfeld',
        'categoria': 'Bolsos',
        'descripcion': 'Bolso crossbody compacto con correa ajustable y compartimento principal con cierre.',
        'precio': '799000.00',
        'talla': 'Única',
        'color': 'Negro',
        'stock': 3,
        'imagen_url': 'https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Morrál de cuero Mario Hernandez',
        'marca': 'Mario Hernandez',
        'categoria': 'Morrales',
        'descripcion': 'Morral de cuero con cierre superior, asas ajustables y compartimento interior.',
        'precio': '1199000.00',
        'talla': 'Única',
        'color': 'Marrón',
        'stock': 3,
        'imagen_url': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Billetera de cuero Mario Hernandez',
        'marca': 'Mario Hernandez',
        'categoria': 'Accesorios',
        'descripcion': 'Billetera compacta de cuero con ranuras para tarjetas y compartimento para billetes.',
        'precio': '389000.00',
        'talla': 'Única',
        'color': 'Negro',
        'stock': 7,
        'imagen_url': 'https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Tenis Suede Classic XXI Puma',
        'marca': 'Puma',
        'categoria': 'Calzado',
        'descripcion': 'Tenis de perfil bajo inspirados en el modelo Suede, con exterior de acabado tipo gamuza.',
        'precio': '399000.00',
        'talla': '40',
        'color': 'Negro y blanco',
        'stock': 6,
        'imagen_url': 'https://images.unsplash.com/photo-1495555961986-6d4c1ecb7be3?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Camiseta Essentials Logo Puma',
        'marca': 'Puma',
        'categoria': 'Camisetas',
        'descripcion': 'Camiseta básica de algodón con logo frontal y corte cómodo.',
        'precio': '159000.00',
        'talla': 'L',
        'color': 'Blanco',
        'stock': 12,
        'imagen_url': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Perfume BOSS Bottled Eau de Toilette',
        'marca': 'Hugo Boss',
        'categoria': 'Perfumes',
        'descripcion': 'Fragancia BOSS Bottled en presentación Eau de Toilette para uso diario.',
        'precio': '469000.00',
        'talla': '100 ml',
        'color': 'Transparente',
        'stock': 5,
        'imagen_url': 'https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Hoodie con logo BOSS',
        'marca': 'Hugo Boss',
        'categoria': 'Hoodies',
        'descripcion': 'Buzo de algodón con capucha, puños acanalados y logo discreto.',
        'precio': '699000.00',
        'talla': 'L',
        'color': 'Gris',
        'stock': 4,
        'imagen_url': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=900&q=85',
    },
    {
        'nombre': 'Tenis casual BOSS',
        'marca': 'Hugo Boss',
        'categoria': 'Calzado',
        'descripcion': 'Tenis casual de diseño minimalista con cordones y suela de goma.',
        'precio': '899000.00',
        'talla': '41',
        'color': 'Blanco',
        'stock': 3,
        'imagen_url': 'https://images.unsplash.com/photo-1600185365483-26d7a4cc7519?auto=format&fit=crop&w=900&q=85',
    },
]


class Command(BaseCommand):
    help = 'Crea o actualiza 20 productos MH’ELEGANZA y su inventario inicial.'

    @transaction.atomic
    def handle(self, *args, **options):
        for registro in PRODUCTOS:
            datos = registro.copy()
            stock = datos.pop('stock')
            producto, _ = Producto.objects.update_or_create(
                nombre=datos['nombre'],
                defaults={
                    **datos,
                    'disponible': stock > 0,
                },
            )
            Inventario.objects.get_or_create(
                producto=producto,
                defaults={'stock_actual': stock, 'stock_minimo': 3},
            )
            VarianteProducto.objects.get_or_create(
                producto=producto,
                talla=datos['talla'],
                defaults={'stock': stock},
            )
            if datos['imagen_url']:
                ImagenProducto.objects.get_or_create(
                    producto=producto,
                    imagen_url=datos['imagen_url'],
                    defaults={'orden': 0},
                )

        self.stdout.write(self.style.SUCCESS(
            f'{len(PRODUCTOS)} productos MH’ELEGANZA están listos.'
        ))
