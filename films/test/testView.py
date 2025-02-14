from ..models import Film, Ratings
from django.test import TestCase
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import shutil
from django.core.cache import cache


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
        self.assertTemplateUsed(response, 'films/start_notLogged.html')
        # Check if 'all' (films) is present in the context
        self.assertIn('all', response.context)
        self.assertEqual(len(response.context['all']), 1)

    def test_start_view_logged_in(self):
        """Test the start view for a logged-in user."""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('start'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'films/startLogged.html')
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
        self.assertTemplateUsed(response, 'films/add_films.html')

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
