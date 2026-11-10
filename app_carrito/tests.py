from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from app_inventario.models import Inventario
from app_productos.models import Producto, VarianteProducto


class CarritoStockTests(TestCase):
	def setUp(self):
		self.producto = Producto.objects.create(
			nombre='Camisa QA', descripcion='Producto de prueba', precio='100.00',
			categoria='Camisas', talla='M', color='Azul', marca='MH', disponible=True,
		)
		Inventario.objects.create(producto=self.producto, stock_actual=1)
		usuario = get_user_model().objects.create_user(
			username='cliente@example.com',
			email='cliente@example.com',
			password='Cliente_123',
		)
		self.client.force_login(usuario)

	def test_agrega_producto_disponible_al_carrito(self):
		response = self.client.post(reverse('agregar_carrito', args=[self.producto.pk]))

		self.assertRedirects(response, reverse('ver_carrito'))
		self.assertEqual(self.client.session['carrito'][str(self.producto.pk)]['cantidad'], 1)

	def test_rechaza_cantidad_superior_al_stock(self):
		self.client.post(reverse('agregar_carrito', args=[self.producto.pk]))
		response = self.client.post(
			reverse('actualizar_cantidad', args=[self.producto.pk]), {'cantidad': 2}
		)

		self.assertRedirects(response, reverse('ver_carrito'))
		self.assertEqual(self.client.session['carrito'][str(self.producto.pk)]['cantidad'], 1)

	def test_agregar_carrito_respeta_cantidad_seleccionada(self):
		self.inventario = Inventario.objects.get(producto=self.producto)
		self.inventario.stock_actual = 3
		self.inventario.save()

		self.client.post(
			reverse('agregar_carrito', args=[self.producto.pk]),
			{'cantidad': 2},
		)

		self.assertEqual(self.client.session['carrito'][str(self.producto.pk)]['cantidad'], 2)

	def test_mismo_producto_se_agrega_por_talla_como_lineas_independientes(self):
		VarianteProducto.objects.create(producto=self.producto, talla='M', stock=2)
		variante_l = VarianteProducto.objects.create(producto=self.producto, talla='L', stock=3)
		self.inventario = Inventario.objects.get(producto=self.producto)
		self.inventario.stock_actual = 5
		self.inventario.save()
		variante_m = VarianteProducto.objects.get(producto=self.producto, talla='M')

		self.client.post(
			reverse('agregar_carrito', args=[self.producto.pk]),
			{'variante_id': variante_m.pk, 'cantidad': 1},
		)
		self.client.post(
			reverse('agregar_carrito', args=[self.producto.pk]),
			{'variante_id': variante_l.pk, 'cantidad': 2},
		)

		carrito = self.client.session['carrito']
		self.assertEqual(len(carrito), 2)
		self.assertEqual(carrito[f'{self.producto.pk}:{variante_m.pk}']['talla'], 'M')
		self.assertEqual(carrito[f'{self.producto.pk}:{variante_l.pk}']['cantidad'], 2)

	def test_agregar_rechaza_variante_de_otro_producto(self):
		otra_variante = VarianteProducto.objects.create(producto=self.producto, talla='M', stock=1)
		otro_producto = Producto.objects.create(
			nombre='Pantalón QA', descripcion='Producto de prueba', precio='150.00',
			categoria='Pantalones', talla='M', color='Negro', marca='MH', disponible=True,
		)
		Inventario.objects.create(producto=otro_producto, stock_actual=1)

		response = self.client.post(
			reverse('agregar_carrito', args=[otro_producto.pk]),
			{'variante_id': otra_variante.pk, 'cantidad': 1},
		)

		self.assertRedirects(response, reverse('catalogo'))
		self.assertNotIn(str(otro_producto.pk), self.client.session.get('carrito', {}))

	def test_requiere_sesion_para_acceder_al_carrito(self):
		self.client.logout()

		response = self.client.get(reverse('ver_carrito'))

		self.assertRedirects(response, reverse('login') + '?next=' + reverse('ver_carrito'))

	def test_get_no_elimina_un_producto_del_carrito(self):
		session = self.client.session
		session['carrito'] = {
			str(self.producto.pk): {
				'producto_id': self.producto.pk,
				'nombre': self.producto.nombre,
				'precio': 100,
				'cantidad': 1,
			}
		}
		session.save()

		response = self.client.get(reverse('eliminar_carrito_item', args=[self.producto.pk]))

		self.assertRedirects(response, reverse('ver_carrito'))
		self.assertIn(str(self.producto.pk), self.client.session['carrito'])

# Create your tests here.
