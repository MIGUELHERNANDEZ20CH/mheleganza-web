from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.test import TestCase
from django.urls import reverse
import re
from django.test import Client

from .models import PerfilCliente


class RegistroLoginTests(TestCase):
	def test_login_y_registro_entregan_csrf_cookie_y_no_cachean_formularios(self):
		client = Client(enforce_csrf_checks=True)
		for url in (reverse('login'), reverse('registro')):
			response = client.get(url)
			self.assertEqual(response.status_code, 200)
			self.assertIn('csrftoken', response.cookies)
			self.assertIn('no-store', response['Cache-Control'])

			csrf_token = response.cookies['csrftoken'].value
			response = client.post(url, {
				'csrfmiddlewaretoken': csrf_token,
				'identificador': 'no-existe@example.com',
				'password': 'Invalid_123!',
				'nombre': 'Prueba',
				'email': 'csrf@example.com',
				'telefono': '3005550123',
			}, HTTP_X_CSRFTOKEN=csrf_token)
			self.assertNotEqual(response.status_code, 403)

	def test_registro_persiste_cliente_y_redirige_al_catalogo(self):
		response = self.client.post(reverse('registro'), {
			'nombre': 'Ana Pérez',
			'email': 'ana@example.com',
			'telefono': '3005550101',
			'direccion': 'Calle 1',
			'password': 'Eleganza_123',
		})

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('catalogo'))
		response = self.client.get(reverse('catalogo'))
		self.assertContains(response, 'Registro exitoso')
		usuario = get_user_model().objects.get(email='ana@example.com')
		self.assertTrue(usuario.check_password('Eleganza_123'))
		self.assertEqual(usuario.perfil_cliente.telefono, '3005550101')

	def test_correo_duplicado_no_crea_otro_usuario(self):
		usuario = get_user_model().objects.create_user(
			username='ana@example.com', email='ana@example.com', password='Eleganza_123'
		)
		PerfilCliente.objects.update_or_create(
			usuario=usuario,
			defaults={'telefono': '3005550101'},
		)

		response = self.client.post(reverse('registro'), {
			'nombre': 'Ana Pérez',
			'email': 'ANA@example.com',
			'telefono': '3005550102',
			'password': 'Eleganza_123',
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'El correo ya está registrado')
		self.assertContains(response, 'id="registro-feedback" role="alert" hidden')
		self.assertContains(response, 'is-invalid" id="email"')
		self.assertContains(response, 'ANA@example.com')
		self.assertEqual(get_user_model().objects.filter(email__iexact='ana@example.com').count(), 1)

	def test_registro_incompleto_y_correo_invalido_muestra_mensajes_y_resalta_campos(self):
		response = self.client.post(reverse('registro'), {
			'nombre': '',
			'email': 'correo-invalido',
			'telefono': '',
			'password': '',
		})

		self.assertContains(response, 'Campos incompletos')
		self.assertContains(response, 'Correo no válido')
		self.assertContains(response, 'class="form-control rounded-pill px-3 py-2 is-invalid"')

	def test_registro_no_acepta_nombre_o_telefono_vacios_aunque_contrasena_y_correo_sean_validos(self):
		response = self.client.post(reverse('registro'), {
			'nombre': '',
			'email': 'valido@example.com',
			'telefono': '',
			'password': 'Eleganza_123',
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Campos incompletos')
		self.assertFalse(get_user_model().objects.filter(email='valido@example.com').exists())

	def test_login_funciona_con_correo_y_telefono(self):
		usuario = get_user_model().objects.create_user(
			username='ana@example.com', email='ana@example.com', password='Eleganza_123', first_name='Ana'
		)
		PerfilCliente.objects.update_or_create(
			usuario=usuario,
			defaults={'telefono': '3005550101'},
		)

		for identificador in ('ana@example.com', '3005550101'):
			response = self.client.post(reverse('login'), {
				'identificador': identificador,
				'password': 'Eleganza_123',
			})
			self.assertRedirects(response, reverse('catalogo'))

	def test_cerrar_sesion_destruye_sesion_y_redirige_al_login(self):
			usuario = get_user_model().objects.create_user(
				username='ana@example.com', email='ana@example.com', password='Eleganza_123'
			)
			self.client.force_login(usuario)
			session = self.client.session
			session['carrito'] = {'1': {'cantidad': 1}}
			session.save()

			response = self.client.post(reverse('cerrar_sesion'))

			self.assertRedirects(response, reverse('login'))
			self.assertNotIn('_auth_user_id', self.client.session)
			self.assertNotIn('carrito', self.client.session)
			self.client.post(reverse('cerrar_sesion'))

	def test_login_admin_redirige_al_panel_y_cliente_al_catalogo(self):
		User = get_user_model()
		admin = User.objects.create_user(
			username='admin@example.com', email='admin@example.com', password='Admin_123', is_staff=True
		)
		cliente = User.objects.create_user(
			username='cliente@example.com', email='cliente@example.com', password='Cliente_123'
		)
		PerfilCliente.objects.update_or_create(
			usuario=admin,
			defaults={'telefono': '3005550103', 'rol': 'admin'},
		)
		PerfilCliente.objects.update_or_create(
			usuario=cliente,
			defaults={'telefono': '3005550104'},
		)

		response_admin = self.client.post(reverse('login'), {
			'identificador': 'admin@example.com', 'password': 'Admin_123',
		})
		self.assertRedirects(response_admin, reverse('admin_productos'))
		self.client.post(reverse('cerrar_sesion'))

		response_cliente = self.client.post(reverse('login'), {
			'identificador': 'cliente@example.com', 'password': 'Cliente_123',
		})
		self.assertRedirects(response_cliente, reverse('catalogo'))

	@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
	def test_recuperacion_envia_codigo_y_actualiza_contrasena(self):
		usuario = get_user_model().objects.create_user(
			username='ana@example.com', email='ana@example.com', password='Eleganza_123'
		)
		PerfilCliente.objects.update_or_create(
			usuario=usuario,
			defaults={'telefono': '3005550101'},
		)

		response = self.client.post(reverse('recuperar_contrasena'), {'email': 'ana@example.com'})
		self.assertRedirects(response, reverse('password_reset_done'))
		self.assertEqual(len(mail.outbox), 1)
		confirm_path = re.search(
			r'https?://[^/]+(?P<path>/usuarios/password-reset/confirmar/\S+)',
			mail.outbox[0].body,
		).group('path').strip()
		confirm_response = self.client.get(confirm_path)
		self.assertEqual(confirm_response.status_code, 302)
		confirm_path = confirm_response.url

		response = self.client.post(confirm_path, {
			'new_password1': 'NuevaClave_123',
			'new_password2': 'NuevaClave_123',
		})

		self.assertRedirects(response, reverse('password_reset_complete'))
		usuario.refresh_from_db()
		self.assertTrue(usuario.check_password('NuevaClave_123'))

	def test_actualizacion_perfil_guarda_datos_y_rechaza_correo_existente(self):
		usuario = get_user_model().objects.create_user(
			username='ana@example.com', email='ana@example.com', password='Eleganza_123', first_name='Ana'
		)
		PerfilCliente.objects.update_or_create(
			usuario=usuario,
			defaults={'telefono': '3005550101'},
		)
		otro = get_user_model().objects.create_user(
			username='otro@example.com', email='otro@example.com', password='Eleganza_123'
		)
		PerfilCliente.objects.update_or_create(
			usuario=otro,
			defaults={'telefono': '3005550102'},
		)
		self.client.force_login(usuario)

		response = self.client.post(reverse('actualizar_perfil'), {
			'nombre': 'Ana María', 'email': 'otro@example.com', 'telefono': '3005550101',
		})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Correo existente')
		self.assertContains(response, 'value="otro@example.com"')
		usuario.refresh_from_db()
		self.assertEqual(usuario.email, 'ana@example.com')

		response = self.client.post(reverse('actualizar_perfil'), {
			'nombre': 'Ana María', 'email': 'ana.nueva@example.com', 'telefono': '3005550199',
		})
		self.assertRedirects(response, reverse('perfil_datos'))
		usuario.refresh_from_db()
		self.assertEqual(usuario.email, 'ana.nueva@example.com')
		self.assertEqual(usuario.perfil_cliente.telefono, '3005550199')
