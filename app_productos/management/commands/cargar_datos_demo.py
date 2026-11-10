from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from app_inventario.models import Inventario
from app_productos.models import ImagenProducto, Producto, VarianteProducto
from app_usuarios.models import PerfilCliente


PRODUCTOS = [
    {
        'nombre': 'Vestido midi floral Aurora',
        'descripcion': 'Vestido midi de silueta fluida con estampado floral, escote cruzado y cintura ajustable. Ideal para eventos de día.',
        'precio': '189900.00', 'categoria': 'Vestidos', 'talla': 'M', 'color': 'Floral multicolor', 'marca': 'MH Eleganza',
        'imagen_url': 'https://images.unsplash.com/photo-1612336307429-8a898d10e223?auto=format&fit=crop&w=900&q=85', 'stock': 12,
    },
    {
        'nombre': 'Blusa de lino Serena',
        'descripcion': 'Blusa de lino ligero con botones frontales, manga larga remangable y corte relajado para uso diario.',
        'precio': '99900.00', 'categoria': 'Blusas', 'talla': 'S', 'color': 'Blanco', 'marca': 'MH Eleganza',
        'imagen_url': 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=900&q=85', 'stock': 18,
    },
    {
        'nombre': 'Jean recto clásico',
        'descripcion': 'Jean de tiro medio y pierna recta, confeccionado en denim resistente con cinco bolsillos y cierre de botón.',
        'precio': '159900.00', 'categoria': 'Pantalones', 'talla': '28', 'color': 'Azul índigo', 'marca': 'MH Denim',
        'imagen_url': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=900&q=85', 'stock': 15,
    },
    {
        'nombre': 'Blazer sastre Verona',
        'descripcion': 'Blazer estructurado de corte sastre con solapa clásica, forro interior y bolsillos funcionales.',
        'precio': '249900.00', 'categoria': 'Chaquetas', 'talla': 'M', 'color': 'Negro', 'marca': 'MH Eleganza',
        'imagen_url': 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?auto=format&fit=crop&w=900&q=85', 'stock': 8,
    },
    {
        'nombre': 'Falda plisada Olivia',
        'descripcion': 'Falda midi plisada con pretina cómoda y caída elegante, fácil de combinar para ocasiones formales o casuales.',
        'precio': '139900.00', 'categoria': 'Faldas', 'talla': 'S', 'color': 'Verde oliva', 'marca': 'MH Eleganza',
        'imagen_url': 'https://images.unsplash.com/photo-1583496661160-fb5886a0aaaa?auto=format&fit=crop&w=900&q=85', 'stock': 10,
    },
    {
        'nombre': 'Bolso de hombro Siena',
        'descripcion': 'Bolso compacto de hombro con correa ajustable, cierre superior y compartimento interior para esenciales.',
        'precio': '179900.00', 'categoria': 'Accesorios', 'talla': 'Única', 'color': 'Marrón', 'marca': 'MH Accesorios',
        'imagen_url': 'https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=900&q=85', 'stock': 7,
    },
    {
        'nombre': 'Tenis urbanos Nube',
        'descripcion': 'Tenis livianos de uso diario con exterior textil transpirable, plantilla acolchada y suela de buen agarre.',
        'precio': '219900.00', 'categoria': 'Calzado', 'talla': '37', 'color': 'Blanco', 'marca': 'MH Urban',
        'imagen_url': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=85', 'stock': 11,
    },
    {
        'nombre': 'Chaqueta denim clásica',
        'descripcion': 'Chaqueta de denim de silueta clásica con botones metálicos, bolsillos delanteros y acabado de lavado medio.',
        'precio': '199900.00', 'categoria': 'Chaquetas', 'talla': 'L', 'color': 'Azul claro', 'marca': 'MH Denim',
        'imagen_url': 'https://images.unsplash.com/photo-1543076447-215ad9ba6923?auto=format&fit=crop&w=900&q=85', 'stock': 9,
    },
    {
        'nombre': 'Camisa Oxford esencial',
        'descripcion': 'Camisa de algodón tipo Oxford con cuello clásico, puños abotonados y corte versátil para oficina o fin de semana.',
        'precio': '129900.00', 'categoria': 'Camisas', 'talla': 'M', 'color': 'Celeste', 'marca': 'MH Essentials',
        'imagen_url': 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=900&q=85', 'stock': 14,
    },
    {
        'nombre': 'Collar dorado Nerea',
        'descripcion': 'Collar de eslabones finos con acabado dorado y cierre ajustable. Un accesorio ligero para complementar cualquier conjunto.',
        'precio': '69900.00', 'categoria': 'Accesorios', 'talla': 'Única', 'color': 'Dorado', 'marca': 'MH Accesorios',
        'imagen_url': 'https://images.unsplash.com/photo-1611652022419-a9419f74343d?auto=format&fit=crop&w=900&q=85', 'stock': 20,
    },
]


class Command(BaseCommand):
    help = 'Crea productos, inventario y cuentas de demostración para el catálogo.'

    @transaction.atomic
    def handle(self, *args, **options):
        for registro in PRODUCTOS:
            datos = dict(registro)
            stock = datos.pop('stock')
            producto, _ = Producto.objects.update_or_create(
                nombre=datos['nombre'],
                defaults={**datos, 'disponible': stock > 0},
            )
            Inventario.objects.update_or_create(
                producto=producto,
                defaults={'stock_actual': stock, 'stock_minimo': 3},
            )
            VarianteProducto.objects.update_or_create(
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

        User = get_user_model()
        self._crear_cuenta(User, 'admin@mheleganza.com', 'Admin123!', 'Administradora', '3000000001', 'admin', True)
        self._crear_cuenta(User, 'cliente@mheleganza.com', 'Cliente123!', 'Cliente Demostración', '3000000002', 'cliente', False)
        self.stdout.write(self.style.SUCCESS('10 productos y las cuentas de demostración están listos.'))

    def _crear_cuenta(self, user_model, email, password, nombre, telefono, rol, es_admin):
        usuario, creado = user_model.objects.get_or_create(
            username=email,
            defaults={
                'email': email,
                'first_name': nombre,
                'is_staff': es_admin,
                'is_superuser': es_admin,
                'is_active': True,
            },
        )
        if creado:
            usuario.set_password(password)
            usuario.save(update_fields=['password'])
        elif es_admin and not usuario.is_staff:
            usuario.is_staff = True
            usuario.is_superuser = True
            usuario.save(update_fields=['is_staff', 'is_superuser'])

        PerfilCliente.objects.update_or_create(
            usuario=usuario,
            defaults={'telefono': telefono, 'rol': rol},
        )