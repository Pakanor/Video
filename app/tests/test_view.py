from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib import messages
from unittest.mock import patch
from django.core.exceptions import ValidationError


class RegisterViewTest(TestCase):
    def setUp(self):
        # Zmienna 'register' powinna być zamieniona na odpowiednią nazwę URL-a
        self.url = reverse('register')

    def test_register_view_get_not_logged(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_register_view_get_logged(self):
        self.user = User.objects.create_user(username="123", password="123")

        self.client.login(username='123', password='123')
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('start'))
