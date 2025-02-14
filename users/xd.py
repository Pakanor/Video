from django.test import TestCase
from django.test import TestCase
from users.tokens import account_activation_token
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch
from django.contrib.messages import get_messages
from .forms import RegisterForm, LoginForm, EmailForm
from django.core.exceptions import ValidationError


class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPass123!'
        }

    def test_register_successful(self):
        with patch('users.views.token') as mock_token:
            response = self.client.post(self.register_url, self.user_data)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'users/register.html')
            self.assertTrue(User.objects.filter(username='testuser').exists())
            user = User.objects.get(username='testuser')
            # Sprawdź False zamiast ręcznie ustawiać 0
            self.assertFalse(user.is_active)

            self.assertFalse(user.is_active)

    def test_register_invalid_password(self):
        with patch('users.views.custom_validate_password', side_effect=ValidationError("Your password is not strong enough. Please try again.")):
            response = self.client.post(
                self.register_url, {**self.user_data, 'password': 'weak'}, follow=True)

            messages = list(get_messages(response.wsgi_request))

            # Powinna być dokładnie jedna wiadomość
            self.assertEqual(len(messages), 1)

            self.assertTrue(any(
                "Your password is not strong enough. Please try again." in str(m) for m in messages))

    def test_register_existing_username(self):

        response = self.client.post(
            self.register_url, self.user_data, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Login or email already in use" in str(m)
                        for m in messages))

    def test_register_existing_email(self):
        User.objects.create_user(
            username='otheruser', email='test@example.com', password='StrongPass123!')
        response = self.client.post(self.register_url, self.user_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Login or email already in use" in str(m)
                            for m in messages))

    def test_login_non_existent_email(self):
        response = self.client.post(self.login_url, {
                                    'email': 'nonexistent@example.com', 'password': 'StrongPass123!'})
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("nie istnieje taki email" in str(m)
                            for m in messages))
