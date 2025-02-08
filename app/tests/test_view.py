from ..models import Film, Ratings
from app.models import Film
from django.test import TestCase
from app.tokens import account_activation_token
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch
from django.contrib.messages import get_messages
from ..forms import RegisterForm, LoginForm, EmailForm
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import shutil
from ..models import Film
from django.core.cache import cache


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
        self.assertTemplateUsed(response, 'register.html')
        self.assertIsInstance(response.context['form'], RegisterForm)

    def test_register_successful(self):
        with patch('app.views.token') as mock_token:
            response = self.client.post(self.register_url, self.user_data)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'email_verification.html')
            self.assertTrue(User.objects.filter(username='testuser').exists())
            user = User.objects.get(username='testuser')
            self.assertFalse(user.is_active)
            mock_token.assert_called_once()

    def test_register_existing_username(self):
        User.objects.create_user(
            username='testuser', email='test@example.com', password='StrongPass123!')
        response = self.client.post(self.register_url, self.user_data)
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

    def test_register_invalid_password(self):
        with patch('app.views.validate_password', side_effect=ValidationError("Weak password")):
            response = self.client.post(
                self.register_url, {**self.user_data, 'password': 'weak'})
            messages = list(get_messages(response.wsgi_request))
            self.assertTrue(any("Weak password" in str(m) for m in messages))


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
        self.assertTemplateUsed(response, 'login.html')
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

    def test_login_non_existent_email(self):
        response = self.client.post(self.login_url, {
                                    'email': 'nonexistent@example.com', 'password': 'StrongPass123!'})
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("nie istnieje taki email" in str(m)
                        for m in messages))

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
        self.assertTemplateUsed(response, 'email_for_password_change.html')
        self.assertIsInstance(response.context['form'], EmailForm)

    def test_email_successful(self):
        with patch('app.views.token') as mock_token:
            response = self.client.post(
                self.email_url, {'email': 'test@example.com'})
            messages = list(get_messages(response.wsgi_request))
            self.assertTrue(
                any("succesfuly send to test@example.com" in str(m) for m in messages))
            mock_token.assert_called_once()

    def test_email_non_existent_user(self):
        response = self.client.post(
            self.email_url, {'email': 'ssss@o2.com'})
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("User matching query does not exist." in str(m) for m in messages))


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

        self.assertTemplateUsed(response, 'register.html')

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

        self.assertTemplateUsed(response, 'register.html')

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

        self.assertTemplateUsed(response, 'register.html')


# Temporary directory for test files
@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class StartViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a test user
        cls.user = User.objects.create_user(
            username='testuser', password='testpassword')

        # Create test files for `thumbnail`
        cls.thumbnail = SimpleUploadedFile(
            "thumbnail.jpg", b"file_content", content_type="image/jpeg")
        cls.video_file = SimpleUploadedFile(
            "video.mp4", b"file_content", content_type="video/mp4")

        # Create a test film
        cls.film = Film.objects.create(
            name="Test Film",
            description="Test Description",
            link=cls.video_file,
            thumbnail=cls.thumbnail
        )

    @classmethod
    def tearDownClass(cls):
        # Remove the temporary test directory after tests
        shutil.rmtree(tempfile.gettempdir(), ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = Client()
        cache.clear()  # Clear cache before each test

    def test_start_view_not_logged_in(self):
        """Test the start view for an unauthenticated user."""
        response = self.client.get(reverse('start'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'start_notLogged.html')
        # Check if 'all' (films) is present in the context
        self.assertIn('all', response.context)
        self.assertEqual(len(response.context['all']), 1)

    def test_start_view_logged_in(self):
        """Test the start view for a logged-in user."""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('start'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'startLogged.html')
        self.assertIn('all', response.context)
        self.assertEqual(len(response.context['all']), 1)
        # There should be a review form
        self.assertIn('form', response.context)

    def test_start_view_caching(self):
        """Test if caching works correctly."""
        cache.set('films_list', [self.film], timeout=3600)
        response = self.client.get(reverse('start'))
        self.assertEqual(response.status_code, 200)
        # Should use cached data
        self.assertEqual(len(response.context['all']), 1)

    def test_start_view_cache_miss(self):
        """Test if films are retrieved from the database when cache is empty."""
        cache.clear()
        response = self.client.get(reverse('start'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['all']), 1)

    def test_start_view_no_films(self):
        """Test the start view when no films exist in the database."""
        Film.objects.all().delete()
        response = self.client.get(reverse('start'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['all']), 0)  # No films available

    def test_start_view_multiple_films(self):
        """Test if multiple films are correctly rendered in the view."""
        Film.objects.create(
            name="Another Film",
            description="Another Description",
            link=self.video_file,
            thumbnail=self.thumbnail
        )
        response = self.client.get(reverse('start'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['all']), 2)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class AddVideoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a superuser for testing
        cls.admin_user = User.objects.create_superuser(
            username='admin', password='adminpassword')

        # Create a normal user
        cls.normal_user = User.objects.create_user(
            username='testuser', password='testpassword')

        # Sample video and thumbnail files
        cls.video_file = SimpleUploadedFile(
            "video.mp4", b"file_content", content_type="video/mp4")
        cls.thumbnail = SimpleUploadedFile(
            "thumbnail.jpg", b"file_content", content_type="image/jpeg")

    @classmethod
    def tearDownClass(cls):
        # Remove temporary media directory after tests
        shutil.rmtree(tempfile.gettempdir(), ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = Client()
        cache.clear()  # Clear cache before each test

    def test_access_denied_for_non_admin(self):
        """Ensure that non-admin users cannot access the add video page."""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('add_video'))
        self.assertEqual(response.status_code, 403)

    def test_access_granted_for_admin(self):
        """Ensure that admin users can access the add video page."""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('add_video'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_films.html')

    def test_successful_video_upload(self):
        """Ensure a superuser can successfully upload a video."""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.post(reverse('add_video'), {
            'video_name': 'Test Video',
            'video_description': 'Test Description',
            'link': self.video_file,
            'thumbnail': self.thumbnail
        }, format='multipart')
        self.assertEqual(Film.objects.count(), 1)
        self.assertRedirects(response, f"/watch/{Film.objects.first().id}")

    def test_invalid_video_format(self):
        """Ensure that uploading a non-MP4 file is rejected."""
        self.client.login(username='admin', password='adminpassword')
        invalid_video = SimpleUploadedFile(
            "video.avi", b"file_content", content_type="video/avi")
        response = self.client.post(reverse('add_video'), {
            'video_name': 'Test Video',
            'video_description': 'Test Description',
            'link': invalid_video,
            'thumbnail': self.thumbnail
        }, format='multipart')
        self.assertEqual(Film.objects.count(), 0)
        self.assertContains(response, "upload an mp4 file!")


class VideoViewerTestCase(TestCase):
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(
            username='testuser', password='testpassword')

        # Create a film for testing
        self.film = Film.objects.create(
            name='Test Film',
            description='A test description for the film.',
            link='films/testfilm.mp4',
            thumbnail='films/testthumbnail.jpg'
        )

        # URL for the film viewing page
        self.url = reverse('watch', args=[self.film.id])

    def test_get_request_no_ratings_in_cache(self):
        # Assuming a user object exists, use a test user.
        self.client.login(username='testuser', password='testpassword')

        # Now make the GET request
        response = self.client.get(self.url)

        # Assert the response status is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Check if the film name is in the response
        self.assertContains(response, self.film.name)

    def test_get_request_with_ratings_in_cache(self):
        # Ensure there are ratings in the database for the film
        film = Film.objects.create(
            name="Film Title", description="A description", link="link_to_film", thumbnail="thumbnail_path")
        user = User.objects.create_user(
            username="test", password="password")
        Ratings.objects.create(user=user, film=film,
                               rating=5, comments="Great movie!")

        # Preload ratings in the cache
        cache.set('ratings', Ratings.objects.filter(
            film_id=film.id), timeout=3600)

        # Now make the GET request
        response = self.client.get(self.url)

        # Assert the response status is 302 (redirect)
        self.assertEqual(response.status_code, 302)

        # Fetch ratings from cache and ensure they are populated
        ratings = cache.get('ratings')
        self.assertGreater(len(ratings), 0)  # Ensure there are ratings

    def test_post_request_create_rating(self):
        # Login the user
        self.client.login(username='testuser', password='testpassword')

        # Define the data for the rating form
        data = {'comments': 'Great film!'}

        # Make POST request to submit a rating
        response = self.client.post(self.url, data)

        # Assert the user is redirected after posting the rating
        self.assertRedirects(response, reverse('watch', args=[self.film.id]))

        # Verify that the rating was saved in the database
        rating = Ratings.objects.filter(film=self.film, user=self.user).first()
        self.assertIsNotNone(rating)
        self.assertEqual(rating.comments, 'Great film!')

    def test_post_request_duplicate_rating(self):
        # Login the user
        self.client.login(username='testuser', password='testpassword')

        # First rating submission
        data = {'comments': 'Awesome movie!'}
        self.client.post(self.url, data)

        # Attempt to submit a second rating for the same film
        response = self.client.post(self.url, data)

        # Ensure the user is redirected without submitting a duplicate rating
        self.assertRedirects(response, reverse('watch', args=[self.film.id]))

        # Check that only one rating exists for the film and user
        self.assertEqual(Ratings.objects.filter(
            film=self.film, user=self.user).count(), 1)

    def test_post_request_without_login(self):
        # Try to submit a rating without being logged in
        data = {'comments': 'Nice film!'}

        # Make POST request while not logged in
        response = self.client.post(self.url, data)

        # Assert that the user is redirected to the login page
        self.assertRedirects(response, f'/login?next={self.url}')
