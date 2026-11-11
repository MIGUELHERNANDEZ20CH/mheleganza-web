from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from app_inventario.models import Inventario, MovimientoInventario
from app_productos.models import Producto

from .models import Pedido
from .services import enviar_confirmacion_pedido


class StripeCheckoutTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='stripe@example.com',
            email='stripe@example.com',
            password='SecurePass_123!',
        )
        self.product = Producto.objects.create(
            nombre='Vestido de prueba',
            descripcion='Producto para pruebas de pago',
            precio='250.00',
            categoria='Vestidos',
            talla='M',
            color='Negro',
            marca='MH',
            disponible=True,
        )
        self.inventory = Inventario.objects.create(producto=self.product, stock_actual=3)
        self.client.force_login(self.user)
        session = self.client.session
        session['carrito'] = {
            str(self.product.pk): {
                'producto_id': self.product.pk,
                'cantidad': 2,
                'precio': 1,
                'nombre': 'Precio manipulado por cliente',
            },
        }
        session.save()

    @override_settings(STRIPE_SECRET_KEY='sk_test_key', STRIPE_CURRENCY='cop')
    @patch('app_pedido.views_checkout.stripe.checkout.Session.create')
    def test_stripe_checkout_uses_database_price_and_does_not_decrement_stock(self, create_session):
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
        order = Pedido.objects.get(cliente=self.user)
        self.assertEqual(order.total, 500)
        self.assertEqual(order.estado, 'PENDIENTE')
        self.assertEqual(order.stripe_checkout_session_id, 'cs_test_checkout')
        line_item = create_session.call_args.kwargs['line_items'][0]
        self.assertEqual(line_item['price_data']['unit_amount'], 25000)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_actual, 3)

    @override_settings(
        STRIPE_SECRET_KEY='sk_test_key',
        STRIPE_WEBHOOK_SECRET='whsec_test_key',
        STRIPE_CURRENCY='cop',
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    @patch('app_pedido.webhooks.enviar_alerta_nuevo_pedido')
    @patch('app_pedido.webhooks.enviar_confirmacion_pedido')
    @patch('app_pedido.webhooks.stripe.Webhook.construct_event')
    def test_paid_webhook_is_idempotent_for_inventory(
        self,
        construct_event,
        send_confirmation,
        send_admin_alert,
    ):
        order = Pedido.objects.create(
            cliente=self.user,
            metodo_pago='TARJETA',
            total='500.00',
            direccion_envio='Calle 10 # 5-20',
            stripe_checkout_session_id='cs_test_checkout',
        )
        order.items.create(
            producto=self.product,
            talla='M',
            cantidad=2,
            precio_unitario='250.00',
        )
        stripe_session = {
            'id': 'cs_test_checkout',
            'client_reference_id': str(order.pk),
            'metadata': {'pedido_id': str(order.pk)},
            'payment_intent': 'pi_test_payment',
            'amount_total': 50000,
            'currency': 'cop',
            'payment_status': 'paid',
        }
        construct_event.return_value = {
            'type': 'checkout.session.completed',
            'data': {'object': stripe_session},
        }

        for _ in range(2):
            response = self.client.post(
                reverse('stripe_webhook'),
                data=b'{}',
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='test-signature',
            )
            self.assertEqual(response.status_code, 200)

        order.refresh_from_db()
        self.inventory.refresh_from_db()
        self.assertEqual(order.estado, 'PAGADO')
        self.assertEqual(order.stripe_payment_intent_id, 'pi_test_payment')
        self.assertEqual(self.inventory.stock_actual, 1)
        self.assertEqual(MovimientoInventario.objects.filter(tipo='VENTA').count(), 1)
        send_admin_alert.assert_called_once_with(str(order.pk))

    @override_settings(
        STRIPE_SECRET_KEY='sk_test_key',
        STRIPE_WEBHOOK_SECRET='whsec_test_key',
        STRIPE_CURRENCY='cop',
    )
    @patch('app_pedido.webhooks.stripe.Refund.create')
    @patch('app_pedido.webhooks.stripe.Webhook.construct_event')
    def test_paid_webhook_refunds_when_stock_was_sold_before_confirmation(
        self,
        construct_event,
        create_refund,
    ):
        self.inventory.stock_actual = 1
        self.inventory.save(update_fields=['stock_actual'])
        order = Pedido.objects.create(
            cliente=self.user,
            metodo_pago='TARJETA',
            total='500.00',
            direccion_envio='Calle 10 # 5-20',
            stripe_checkout_session_id='cs_test_checkout',
        )
        order.items.create(
            producto=self.product,
            talla='M',
            cantidad=2,
            precio_unitario='250.00',
        )
        construct_event.return_value = {
            'type': 'checkout.session.completed',
            'data': {'object': {
                'id': 'cs_test_checkout',
                'client_reference_id': str(order.pk),
                'metadata': {'pedido_id': str(order.pk)},
                'payment_intent': 'pi_test_payment',
                'amount_total': 50000,
                'currency': 'cop',
                'payment_status': 'paid',
            }},
        }

        response = self.client.post(
            reverse('stripe_webhook'),
            data=b'{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test-signature',
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.inventory.refresh_from_db()
        self.assertEqual(order.estado, 'RECHAZADO')
        self.assertEqual(self.inventory.stock_actual, 1)
        self.assertFalse(MovimientoInventario.objects.filter(tipo='VENTA').exists())
        create_refund.assert_called_once_with(
            payment_intent='pi_test_payment',
            api_key='sk_test_key',
            idempotency_key=f'mheleganza-stock-refund-{order.pk}',
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_order_confirmation_email_has_html_and_is_sent_once(self):
        order = Pedido.objects.create(
            cliente=self.user,
            metodo_pago='TARJETA',
            total='250.00',
            direccion_envio='Calle 10 # 5-20',
            estado='PAGADO',
        )
        order.items.create(
            producto=self.product,
            talla='M',
            cantidad=1,
            precio_unitario='250.00',
        )

        self.assertTrue(enviar_confirmacion_pedido(order.pk))
        self.assertTrue(enviar_confirmacion_pedido(order.pk))

        order.refresh_from_db()
        self.assertTrue(order.confirmacion_email_enviada)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertEqual(mail.outbox[0].alternatives[0][1], 'text/html')
        self.assertIn(f'#{order.pk}', mail.outbox[0].alternatives[0][0])
