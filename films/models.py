from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.dispatch import receiver

import os


class Film(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=255)
    link = models.FileField(upload_to='videos\\before')
    hls_playlist = models.CharField(
        max_length=255, blank=True, null=True)

    thumbnail = models.ImageField(upload_to='thumbnails/')

    def delete(self, *args, **kwargs):
        """ Usuwa plik przed usunięciem obiektu z bazy """
        if self.link:
            file_path = os.path.join(settings.MEDIA_ROOT, str(self.link))
            if os.path.exists(file_path):
                os.remove(file_path)
        super().delete(*args, **kwargs)


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
