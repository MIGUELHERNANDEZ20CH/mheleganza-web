from django.test import TestCase
from django.urls import reverse

from app_productos.models import Producto, VarianteProducto
from .models import Inventario, MovimientoInventario, NotificacionInventario


class InventarioTests(TestCase):
	def setUp(self):
		self.producto = Producto.objects.create(
			nombre='Producto inventario', descripcion='Prueba', precio='10.00',
			categoria='Ropa', talla='M', color='Negro', marca='MH', disponible=True,
		)
		Inventario.objects.create(producto=self.producto, stock_actual=2)
		session = self.client.session
		session['usuario'] = {'rol': 'admin'}
		session.save()

	def test_salida_agota_stock_y_crea_movimiento_y_notificacion(self):
		response = self.client.post(reverse('registrar_salida'), {
			'producto_id': self.producto.pk,
			'cantidad_salida': 2,
		})

		self.assertRedirects(response, reverse('panel_inventario'))
		inventario = Inventario.objects.get(producto=self.producto)
		self.assertEqual(inventario.stock_actual, 0)
		self.assertEqual(MovimientoInventario.objects.get().tipo, 'SALIDA')
		self.assertTrue(NotificacionInventario.objects.filter(producto=self.producto, leida=False).exists())
		self.producto.refresh_from_db()
		self.assertFalse(self.producto.disponible)

	def test_entrada_actualiza_stock_y_registra_movimiento(self):
		response = self.client.post(reverse('registrar_entrada'), {
			'producto_id': self.producto.pk,
			'cantidad_entrada': 3,
		})

		self.assertRedirects(response, reverse('panel_inventario'))
		inventario = Inventario.objects.get(producto=self.producto)
		self.assertEqual(inventario.stock_actual, 5)
		self.assertEqual(MovimientoInventario.objects.get().tipo, 'ENTRADA')

	def test_entrada_por_talla_sincroniza_el_stock_total(self):
		variante_m = VarianteProducto.objects.create(
			producto=self.producto, talla='M', stock=2,
		)
		variante_l = VarianteProducto.objects.create(
			producto=self.producto, talla='L', stock=1,
		)

		response = self.client.post(reverse('registrar_entrada'), {
			'producto_id': self.producto.pk,
			'variante_id': variante_l.pk,
			'cantidad_entrada': 2,
		})

		self.assertRedirects(response, reverse('panel_inventario'))
		variante_m.refresh_from_db()
		variante_l.refresh_from_db()
		inventario = Inventario.objects.get(producto=self.producto)
		self.assertEqual(variante_m.stock, 2)
		self.assertEqual(variante_l.stock, 3)
		self.assertEqual(inventario.stock_actual, 5)

# Create your tests here.
