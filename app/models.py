from django.db import models
from django.contrib.auth.models import User


class Film(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=30)
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
    user = models.OneToOneField(
        User, on_delete=models.CASCADE)
    film = models.ForeignKey(
        Film, on_delete=models.CASCADE)
    last_watched = models.FloatField()

    def __str__(self):
        return f'Postęp użytkownika {self.user.username} w filmie {self.video_id}'
