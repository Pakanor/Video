from django.test import TestCase
from django.contrib.auth.models import User
from ..models import Film, Ratings, VideoProgress
from django.db import IntegrityError


class FilmModelTest(TestCase):
    def setUp(self):
        self.film = Film.objects.create(
            name="test film",
            description="test description",
            link="test.mp4",
            thumbnail='thumbnail.jpg'
        )

    def test_film_creation(self):
        self.assertEqual(self.film.name, "test film")
        self.assertEqual(self.film.description, "test description")

    def test_max_length_fields(self):
        max_name_length = self.film._meta.get_field('name').max_length
        max_description_length = self.film._meta.get_field(
            'description').max_length
        self.assertEqual(max_name_length, 30)
        self.assertEqual(max_description_length, 255)

# Creating Rating Model Test


class RatingModelTest(TestCase):
    # Creating the user, film and then rating required for the test
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="password")
        self.film = Film.objects.create(
            name="test film",
            description="test description",
            link="test.mp4",
            thumbnail='thumbnail.jpg'
        )
        self.rating = Ratings.objects.create(
            user=self.user, film=self.film, rating=5, comments="example")

# testing if rating is saved
    def test_rating_creation(self):
        self.assertEqual(self.rating.rating, 5)
        self.assertEqual(self.rating.comments, "example")
        self.assertEqual(self.rating.user, self.user)
        self.assertEqual(self.rating.film, self.film)

    # Every user can rate only once test
    def test_user_can_rate_only_once(self):
        with self.assertRaises(Exception):
            Ratings.objects.create(
                user=self.user, film=self.film, rating=4, comments="test")


class VideoProgressTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="password")
        self.film = Film.objects.create(
            name="test film",
            description="test description",
            link="test.mp4",
            thumbnail='thumbnail.jpg'
        )
        self.last_watched = VideoProgress(
            user=self.user, film=self.film, last_watched=10)
# testing if last watched is saved correctly

    def test_video_progress_creation(self):
        self.assertEqual(self.last_watched.last_watched, 10)

    def test_user_can_have_only_one_progress_entry(self):
        # Creating the first record
        VideoProgress.objects.create(
            user=self.user, film=self.film, last_watched=120.5)

        # then trying to create and second record for the same film
        with self.assertRaises(IntegrityError):
            VideoProgress.objects.create(
                user=self.user, film=self.film, last_watched=150.0)

    def test_editing_record_last_watched(self):
        progress = VideoProgress.objects.create(
            user=self.user, film=self.film, last_watched=120.5)
        progress.last_watched = 150
        progress.save()
        updated_progress = VideoProgress.objects.get(
            user=self.user, film=self.film)
        self.assertEqual(updated_progress.last_watched, 150.0)

    def test_str_method(self):
        # looking if method __str__ is correct
        self.assertEqual(str(
            self.last_watched), f"Postęp użytkownika {self.user.username} w filmie {self.film.name}")
