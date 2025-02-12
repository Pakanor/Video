from django.db import models
from django.contrib.auth.models import User


class Film(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=255)
    link = models.FileField(max_length=150)
    thumbnail = models.FileField(max_length=150)


class Ratings(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE)
    film = models.ForeignKey(
        Film, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comments = models.CharField(max_length=250)


class VideoProgress(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE)
    film = models.ForeignKey(
        Film, on_delete=models.CASCADE)
    last_watched = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'film'], name='unique_user_film_progress')
        ]

    def __str__(self):
        return f'Postęp użytkownika {self.user.username} w filmie {self.film.name}'
