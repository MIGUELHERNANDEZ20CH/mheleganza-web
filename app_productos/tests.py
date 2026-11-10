from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from app_inventario.models import Inventario, NotificacionInventario
from .models import ImagenProducto, Producto, VarianteProducto


class CatalogoYProductosTests(TestCase):
	def setUp(self):
		self.producto = Producto.objects.create(
			nombre='Camisa azul', descripcion='Camisa de algodón', precio='100.00',
			categoria='Camisas', talla='M', color='Azul', marca='MH', disponible=True,
		)
		Inventario.objects.create(producto=self.producto, stock_actual=4)

	def test_catalogo_entrega_cookie_csrf_y_no_cachea_formulario_de_agregar(self):
		client = Client(enforce_csrf_checks=True)

		response = client.get(reverse('catalogo'))

		self.assertEqual(response.status_code, 200)
		self.assertIn('csrftoken', response.cookies)
		self.assertIn('no-store', response['Cache-Control'])
		csrf_token = response.cookies['csrftoken'].value
		response = client.post(
			reverse('agregar_carrito', args=[self.producto.pk]),
			{'cantidad': 1, 'csrfmiddlewaretoken': csrf_token},
			HTTP_X_CSRFTOKEN=csrf_token,
		)
		self.assertNotEqual(response.status_code, 403)

	def test_filtros_combinados_muestran_solo_coincidencias(self):
		otro = Producto.objects.create(
			nombre='Chaqueta negra', descripcion='Chaqueta', precio='200.00',
			categoria='Chaquetas', talla='L', color='Negro', marca='MH', disponible=True,
		)
		Inventario.objects.create(producto=otro, stock_actual=2)

		response = self.client.get(reverse('catalogo'), {
			'categoria': 'Camisas',
			'talla': 'M',
			'color': 'Azul',
			'marca': 'MH',
			'precio_min': '50',
			'precio_max': '150',
		})

		self.assertContains(response, 'Camisa azul')
		self.assertNotContains(response, 'Chaqueta negra')
		self.assertContains(response, 'Filtrar')

	def test_quitar_favorito_solo_elimina_con_post(self):
		session = self.client.session
		session['favoritos'] = [self.producto.pk]
		session.save()

		response = self.client.get(reverse('quitar_favorito', args=[self.producto.pk]))
		self.assertRedirects(response, reverse('catalogo'))
		self.assertEqual(self.client.session['favoritos'], [self.producto.pk])

		response = self.client.post(reverse('quitar_favorito', args=[self.producto.pk]))
		self.assertRedirects(response, reverse('catalogo'))
		self.assertEqual(self.client.session['favoritos'], [])

	def test_precio_invalido_muestra_error_en_el_catalogo(self):
		response = self.client.get(reverse('catalogo'), {'precio_min': 'NaN'})

		self.assertContains(response, 'El precio mínimo debe ser un número válido mayor o igual a cero.')
		self.assertContains(response, 'Camisa azul')

	def test_catalogo_muestra_carrusel_de_novedades_y_marcas_disponibles(self):
		for numero in range(4):
			producto = Producto.objects.create(
				nombre=f'Producto destacado {numero}',
				descripcion='Novedad de temporada',
				precio='200.00',
				categoria='Accesorios',
				talla='Única',
				color='Negro',
				marca=f'Marca {numero}',
				imagen_url=f'https://images.example.com/producto-{numero}.jpg',
				disponible=True,
			)
			Inventario.objects.create(producto=producto, stock_actual=2)

		response = self.client.get(reverse('catalogo'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.context['novedades']), 4)
		self.assertContains(response, 'data-shop-carousel')
		self.assertContains(response, 'Marcas disponibles')
		self.assertContains(response, 'Marca 0')
		self.assertContains(response, 'setInterval(showSlide, 5000)')
		self.assertNotContains(response, 'data-shop-next')
		self.assertNotContains(response, 'data-shop-previous')
		self.assertNotContains(response, 'data-shop-toggle')
		self.assertNotContains(response, 'data-shop-dot')

	def test_detalle_muestra_no_disponible_si_el_stock_es_cero(self):
		Inventario.objects.filter(producto=self.producto).update(stock_actual=0)

		response = self.client.get(reverse('detalle_producto', args=[self.producto.pk]))

		self.assertContains(response, 'Producto no disponible')
		self.assertNotContains(response, 'Camisa azul')

	def test_detalle_muestra_galeria_css_y_solo_tallas_con_stock(self):
		VarianteProducto.objects.create(producto=self.producto, talla='M', stock=2)
		VarianteProducto.objects.create(producto=self.producto, talla='L', stock=0)
		ImagenProducto.objects.create(
			producto=self.producto,
			imagen_url='https://images.example.com/camisa-frente.jpg',
		)
		ImagenProducto.objects.create(
			producto=self.producto,
			imagen_url='https://images.example.com/camisa-espalda.jpg',
			orden=1,
		)

		response = self.client.get(reverse('detalle_producto', args=[self.producto.pk]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'type="radio"')
		self.assertContains(response, 'name="imagen-galeria"')
		self.assertContains(response, 'camisa-frente.jpg')
		self.assertContains(response, 'camisa-espalda.jpg')
		self.assertContains(response, '2 disp.')
		self.assertNotContains(response, '0 disp.')

	def test_admin_no_registra_producto_si_faltan_datos_obligatorios(self):
		session = self.client.session
		session['usuario'] = {'rol': 'admin'}
		session.save()

		response = self.client.post(reverse('admin_productos'), {
			'agregar_producto': '1',
			'nombre': '',
			'descripcion': '',
			'precio': '10',
			'stock': '1',
			'categoria': '',
			'talla': '',
			'color': '',
			'marca': '',
		})

		self.assertRedirects(response, reverse('admin_productos'))
		self.assertEqual(Producto.objects.count(), 1)

	def test_admin_registra_producto_y_notifica_stock_agotado(self):
		admin = get_user_model().objects.create_user(
			username='admin@example.com', email='admin@example.com',
			password='Admin_123', is_staff=True,
		)
		self.client.force_login(admin)
		session = self.client.session
		session['usuario'] = {'rol': 'admin'}
		session.save()

		response = self.client.post(reverse('admin_productos'), {
			'agregar_producto': '1',
			'nombre': 'Producto agotado',
			'descripcion': 'Descripción',
			'precio': '10.00',
			'stock': '0',
			'categoria': 'Ropa',
			'talla': 'M',
			'color': 'Negro',
			'marca': 'MH',
			'imagen_url': '',
		})

		self.assertRedirects(response, reverse('admin_productos'))
		producto = Producto.objects.get(nombre='Producto agotado')
		self.assertFalse(producto.disponible)
		self.assertTrue(NotificacionInventario.objects.filter(producto=producto).exists())


class CargarCatalogoMHEleganzaTests(TestCase):
	def test_comando_crea_20_productos_de_las_marcas_solicitadas_y_es_repetible(self):
		call_command('cargar_catalogo_mheleganza', stdout=StringIO())

		self.assertEqual(Producto.objects.count(), 20)
		self.assertEqual(Inventario.objects.count(), 20)
		self.assertSetEqual(
			set(Producto.objects.values_list('marca', flat=True)),
			{
				'Psycho Bunny',
				'Lacoste',
				'Tommy Hilfiger',
				'Under Armour',
				'Karl Lagerfeld',
				'Mario Hernandez',
				'Puma',
				'Hugo Boss',
			},
		)

		inventario = Inventario.objects.order_by('pk').first()
		stock_inicial = inventario.stock_actual
		inventario.stock_actual -= 1
		inventario.save(update_fields=['stock_actual'])
		call_command('cargar_catalogo_mheleganza', stdout=StringIO())

		self.assertEqual(Producto.objects.count(), 20)
		inventario.refresh_from_db()
		self.assertEqual(inventario.stock_actual, stock_inicial - 1)
