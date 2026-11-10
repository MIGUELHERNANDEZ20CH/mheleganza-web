from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import PerfilCliente


class SmsPasswordResetTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='sms@example.com',
            email='sms@example.com',
            password='SecurePass_123!',
        )
        self.profile = PerfilCliente.objects.create(
            usuario=self.user,
            telefono='3005550101',
        )

    @override_settings(
        SMS_OTP_TTL_SECONDS=600,
        SMS_OTP_RESEND_SECONDS=60,
        SMS_OTP_MAX_ATTEMPTS=5,
        TWILIO_DEFAULT_COUNTRY_CODE='57',
    )
    @patch('app_usuarios.views_auth.enviar_sms')
    @patch('app_usuarios.views_auth.secrets.randbelow', return_value=123456)
    def test_sms_otp_is_hashed_verified_and_allows_password_reset(self, random_code, send_sms):
        response = self.client.post(reverse('request_phone_reset'), {
            'telefono': self.profile.telefono,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Si el número está asociado')
        send_sms.assert_called_once()
        self.profile.refresh_from_db()
        self.assertNotEqual(self.profile.sms_code, '123456')
        self.assertEqual(self.profile.sms_code_attempts, 0)

        response = self.client.post(reverse('verify_phone_code'), {'codigo': '123456'})
        self.assertRedirects(response, reverse('set_new_password'))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.sms_code, '')

        response = self.client.post(reverse('set_new_password'), {
            'password_nueva': 'NewSecurePass_456!',
            'password_confirmacion': 'NewSecurePass_456!',
        })

        self.assertRedirects(response, reverse('login'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecurePass_456!'))
