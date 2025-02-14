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

    def test_authenticated_user_redirects(self):
        user = User.objects.create_user(
            username='loggedinuser', email='user@example.com', password='StrongPass123!')
        self.client.force_login(user)
        response = self.client.get(self.register_url)
        self.assertRedirects(response, reverse('start'))

    def test_register_page_loads(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')
        self.assertIsInstance(response.context['form'], RegisterForm)


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='StrongPass123!')

    def test_login_successful(self):
        response = self.client.post(
            self.login_url, {'email': 'test@example.com', 'password': 'StrongPass123!'})
        self.assertRedirects(response, reverse('start'))
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_authenticated_user_redirects(self):
        self.client.force_login(self.user)
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse('start'))

    def test_login_page_loads(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')
        self.assertIsInstance(response.context['form'], LoginForm)

    def test_login_invalid_credentials(self):
        response = self.client.post(
            self.login_url, {'email': 'test@example.com', 'password': 'WrongPass'})
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Wrong password or email" in str(m)
                        for m in messages))

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            self.login_url, {'email': 'test@example.com', 'password': 'StrongPass123!'})
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(f"{self.user.username} not active" in str(m) for m in messages))

    def test_logout(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, '/login')
        self.assertFalse('_auth_user_id' in self.client.session)


class EmailForPasswordChangeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.email_url = reverse('email_for_password_change')
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='StrongPass123!')

    def test_authenticated_user_redirects(self):
        self.client.force_login(self.user)
        response = self.client.get(self.email_url)
        self.assertRedirects(response, reverse('start'))

    def test_email_page_loads(self):
        response = self.client.get(self.email_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'users/email_for_password_change.html')
        self.assertIsInstance(response.context['form'], EmailForm)

    def test_email_successful(self):
        with patch('users.views.token') as mock_token:
            response = self.client.post(
                self.email_url, {'email': 'test@example.com'})
            messages = list(get_messages(response.wsgi_request))

            mock_token.assert_called_once()

    def test_email_non_existent_user(self):
        response = self.client.post(
            self.email_url, {'email': 'ssss@o2.com'})
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("If this email exists in our system, we will send you password reset instructions." in str(m) for m in messages))


class ChangePasswordTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='OldPassword123')
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = account_activation_token.make_token(self.user)
        self.url = reverse('change_password', kwargs={
                           'uidb64': self.uid, 'token': self.token})

    def test_invalid_token(self):
        invalid_url = reverse('change_password', kwargs={
            'uidb64': self.uid, 'token': 'invalid-token'})
        response = self.client.get(invalid_url)
        messages = list(response.context['messages'])
        self.assertTrue(any("bad token or expired" in str(m)
                        for m in messages))

    def test_valid_password_reset(self):
        response = self.client.post(self.url, {
            'password': 'NewPassword123!',
            're_password': 'NewPassword123!'
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123!'))
        self.assertRedirects(response, reverse('login'))

    def test_passwords_do_not_match(self):
        response = self.client.post(self.url, {
            'password': 'NewPassword123!',
            're_password': 'DifferentPassword!'
        })
        messages = list(response.context['messages'])
        self.assertTrue(any("passwords not matching" in str(m)
                        for m in messages))

    def test_non_existent_user(self):
        fake_uid = urlsafe_base64_encode(
            force_bytes(9999))  # Nieistniejący użytkownik
        url = reverse('change_password', kwargs={
                      'uidb64': fake_uid, 'token': self.token})
        response = self.client.post(url, {
            'password': 'NewPassword123!',
            're_password': 'NewPassword123!'
        })
        messages = list(response.context['messages'])
        self.assertTrue(
            any("User matching query does not exist" in str(m) for m in messages))


class TokenValidationTests(TestCase):

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser', password='testpassword', email='test@example.com')
        self.user.is_active = False
        self.user.save()

    def test_valid_token(self):
        token = account_activation_token.make_token(self.user)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.id))
        # Send GET request with valid uid and token
        response = self.client.get(
            reverse('token_validation', args=[uidb64, token]))

        # Ensure that the user is activated
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

        # Check the success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "succes now log in!")

    def test_user_not_found(self):
        # Simulate a scenario where the user does not exist
        invalid_uidb64 = force_bytes(urlsafe_base64_encode(
            force_bytes(99999)))  # Non-existing user ID
        token = 'somefaketoken'

        # Send GET request with invalid user
        response = self.client.get(
            reverse('token_validation', args=[invalid_uidb64, token]))

        # Check that no user is activated and correct error message is shown
        messages = list(response.context['messages'])
        self.assertTrue(any("bad token or expired" in str(m)
                        for m in messages))

        self.assertTemplateUsed(response, 'users/register.html')

    def test_invalid_uidb64(self):
        # Test case where the UID is improperly encoded
        invalid_uidb64 = 'invaliduidb64'
        token = 'somefaketoken'

        # Send GET request with invalid UID
        response = self.client.get(
            reverse('token_validation', args=[invalid_uidb64, token]))

        # Ensure the error message is displayed
        messages = list(response.context['messages'])
        self.assertTrue(any("bad token or expired" in str(m)
                        for m in messages))

        self.assertTemplateUsed(response, 'users/register.html')

    def test_invalid_token(self):
        # Generate a valid token for the test user
        valid_token = account_activation_token.make_token(self.user)
        invalid_token = 'invalidtoken'
        uidb64 = force_bytes(urlsafe_base64_encode(force_bytes(self.user.id)))

        # Send GET request with invalid token
        response = self.client.get(
            reverse('token_validation', args=[uidb64, invalid_token]))

        # Ensure the user is not activated and rendered to the same page with error message
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        messages = list(response.context['messages'])
        self.assertTrue(any("bad token or expired" in str(m)
                        for m in messages))

        self.assertTemplateUsed(response, 'users/register.html')
