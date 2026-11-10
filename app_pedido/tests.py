from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from app_inventario.models import Inventario
from app_productos.models import Producto, VarianteProducto
from .models import Pedido


class CheckoutStockTests(TestCase):
	def setUp(self):
		self.usuario = get_user_model().objects.create_user(
			username='cliente@example.com', email='cliente@example.com', password='Password_123'
		)
		self.producto = Producto.objects.create(
			nombre='Chaqueta QA', descripcion='Producto de prueba', precio='250.00',
			categoria='Chaquetas', talla='M', color='Negro', marca='MH', disponible=True,
		)
		self.inventario = Inventario.objects.create(producto=self.producto, stock_actual=2)
		self.client.force_login(self.usuario)
		session = self.client.session
		session['carrito'] = {
			str(self.producto.pk): {
				'producto_id': self.producto.pk,
				'nombre': self.producto.nombre,
				'precio': 250.0,
				'imagen_url': '',
				'cantidad': 2,
			}
		}
		session.save()

	@override_settings(DEBUG=True)
	def test_checkout_crea_pedido_y_descuenta_stock(self):
		response = self.client.post(reverse('checkout'), {
			'direccion': 'Calle 10 # 5-20',
			'metodo_pago': 'EFECTIVO',
		})

		self.assertRedirects(response, reverse('mis_pedidos'))
		pedido = Pedido.objects.get(cliente=self.usuario)
		self.assertEqual(pedido.total, 500)
		self.assertEqual(pedido.estado, 'PAGADO')
		self.assertEqual(pedido.items.get().cantidad, 2)
		self.inventario.refresh_from_db()
		self.producto.refresh_from_db()
		self.assertEqual(self.inventario.stock_actual, 0)
		self.assertFalse(self.producto.disponible)

	@override_settings(DEBUG=True)
	def test_checkout_descuenta_la_talla_seleccionada_y_la_guarda_en_el_pedido(self):
		variante_m = VarianteProducto.objects.create(
			producto=self.producto, talla='M', stock=1,
		)
		variante_l = VarianteProducto.objects.create(
			producto=self.producto, talla='L', stock=1,
		)
		linea_m = {
			'producto_id': self.producto.pk,
			'variante_id': str(variante_m.pk),
			'talla': 'M',
			'nombre': self.producto.nombre,
			'precio': 250.0,
			'imagen_url': '',
			'cantidad': 1,
		}
		linea_l = {
			**linea_m,
			'variante_id': str(variante_l.pk),
			'talla': 'L',
		}
		session = self.client.session
		session['carrito'] = {
			f'{self.producto.pk}:{variante_m.pk}': {
				**linea_m,
			},
			f'{self.producto.pk}:{variante_l.pk}': {
				**linea_l,
			},
		}
		session.save()

		response = self.client.post(reverse('checkout'), {
			'direccion': 'Calle 10 # 5-20',
			'metodo_pago': 'EFECTIVO',
		})

		self.assertRedirects(response, reverse('mis_pedidos'))
		detalles = Pedido.objects.get(cliente=self.usuario).items.order_by('talla')
		self.assertEqual(list(detalles.values_list('talla', flat=True)), ['L', 'M'])
		variante_m.refresh_from_db()
		variante_l.refresh_from_db()
		self.inventario.refresh_from_db()
		self.assertEqual(variante_m.stock, 0)
		self.assertEqual(variante_l.stock, 0)
		self.assertEqual(self.inventario.stock_actual, 0)

	def test_checkout_bloquea_stock_insuficiente(self):
		self.inventario.stock_actual = 1
		self.inventario.save()

		response = self.client.post(reverse('checkout'), {
			'direccion': 'Calle 10 # 5-20',
			'metodo_pago': 'EFECTIVO',
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Producto no disponible')
		self.assertFalse(Pedido.objects.filter(cliente=self.usuario).exists())
		self.inventario.refresh_from_db()
		self.assertEqual(self.inventario.stock_actual, 1)

	def test_checkout_resalta_y_preserva_campos_de_direccion_y_pago_invalidos(self):
		response = self.client.post(reverse('checkout'), {
			'direccion': '',
			'metodo_pago': 'INVALIDO',
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'id="direccion"')
		self.assertContains(response, 'aria-invalid="true"', count=2)
		self.assertContains(response, 'Ingresa la dirección de envío.')
		self.assertContains(response, 'Selecciona un medio de pago válido.')
		self.assertFalse(Pedido.objects.filter(cliente=self.usuario).exists())
		self.inventario.refresh_from_db()
		self.assertEqual(self.inventario.stock_actual, 2)

	@override_settings(DEBUG=True, STRIPE_SECRET_KEY='sk_test_key')
	@patch('app_pedido.views_checkout.stripe.checkout.Session.create')
	def test_tarjeta_redirige_a_stripe_sin_marcar_pedido_pagado_antes_del_webhook(self, create_session):
		create_session.return_value = SimpleNamespace(
			id='cs_test_checkout',
			url='https://checkout.stripe.test/session',
		)
		response = self.client.post(reverse('checkout'), {
			'direccion': 'Calle 10 # 5-20',
			'metodo_pago': 'TARJETA',
		})

		self.assertRedirects(
			response,
			'https://checkout.stripe.test/session',
			fetch_redirect_response=False,
		)
		pedido = Pedido.objects.get(cliente=self.usuario)
		self.assertEqual(pedido.estado, 'PENDIENTE')
		self.inventario.refresh_from_db()
		self.assertEqual(self.inventario.stock_actual, 2)

	@override_settings(DEBUG=False)
	def test_simulacion_de_pago_se_bloquea_fuera_de_desarrollo(self):
		response = self.client.post(reverse('checkout'), {
			'direccion': 'Calle 10 # 5-20',
			'metodo_pago': 'EFECTIVO',
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Pago rechazado')
		self.assertFalse(Pedido.objects.filter(cliente=self.usuario).exists())
		self.inventario.refresh_from_db()
		self.assertEqual(self.inventario.stock_actual, 2)

	@patch('app_pedido.views.procesar_pago_simulado', return_value=False)
	def test_pago_rechazado_no_crea_pedido_ni_descuenta_stock(self, procesar_pago):
		response = self.client.post(reverse('checkout'), {
			'direccion': 'Calle 10 # 5-20',
			'metodo_pago': 'EFECTIVO',
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Pago rechazado')
		self.assertFalse(Pedido.objects.filter(cliente=self.usuario).exists())
		self.inventario.refresh_from_db()
		self.assertEqual(self.inventario.stock_actual, 2)

	def test_administrador_puede_consultar_detalle_completo_del_pedido(self):
		admin = get_user_model().objects.create_user(
			username='admin@example.com', email='admin@example.com',
			password='Admin_123', is_staff=True,
		)
		pedido = Pedido.objects.create(
			cliente=self.usuario,
			metodo_pago='EFECTIVO',
			total='250.00',
			direccion_envio='Calle 10',
		)
		pedido.items.create(
			producto=self.producto,
			cantidad=1,
			precio_unitario='250.00',
		)
		self.client.force_login(admin)

		response = self.client.get(reverse('detalle_pedido', args=[pedido.pk]))

		self.assertContains(response, 'Calle 10')
		self.assertContains(response, '250')
		self.assertContains(response, 'Chaqueta QA')

	def test_administrador_solo_puede_avanzar_estado_por_transiciones_permitidas(self):
		pedido = Pedido.objects.create(
			cliente=self.usuario,
			metodo_pago='EFECTIVO',
			total='250.00',
			direccion_envio='Calle 10',
		)
		session = self.client.session
		session['usuario'] = {'rol': 'admin'}
		session.save()

		response = self.client.post(reverse('actualizar_estado_pedido', args=[pedido.pk]), {
			'nuevo_estado': 'PAGADO',
		})
		self.assertRedirects(response, reverse('admin_productos'))
		pedido.refresh_from_db()
		self.assertEqual(pedido.estado, 'PAGADO')

		response = self.client.post(reverse('actualizar_estado_pedido', args=[pedido.pk]), {
			'nuevo_estado': 'PENDIENTE',
		})
		self.assertRedirects(response, reverse('admin_productos'))
		pedido.refresh_from_db()
		self.assertEqual(pedido.estado, 'PAGADO')

# Create your tests here.
