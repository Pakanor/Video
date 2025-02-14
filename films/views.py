from .models import Film
from django.shortcuts import render
from django.views.generic import TemplateView
from .models import Film, Ratings, VideoProgress
from .forms import VideoForm, RatingForm
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.cache import cache
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
import os
import subprocess
import ffmpeg
from .tasks import convert_to_hls_task
from django.http import JsonResponse
from celery.result import AsyncResult
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Film
from celery.result import AsyncResult


class startView(TemplateView):
    template_name_logged = 'films/startLogged.html'
    template_name_notlogged = 'films/start_notLogged.html'

    def get(self, request):
        if request.user.is_authenticated:
            form = RatingForm()
            all = cache.get('films_list')
            if not all:
                all = Film.objects.select_related().all()
                cache.set('films_list', all, timeout=3600)
            return render(request, self.template_name_logged, locals())
        else:
            all = Film.objects.select_related().all()

            return render(request, self.template_name_notlogged, locals())


class Add_Video(UserPassesTestMixin, TemplateView):
    template_name = 'films/add_films.html'

    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request):

        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            name = request.POST.get('video_name')
            description = request.POST.get('video_description')
            link = request.FILES['link']
            thumbnail = request.FILES['thumbnail']
            file_type = str(link).split(".")

            if str(file_type[1]) != 'mp4':
                messages.add_message(
                    request, messages.ERROR, "upload an mp4 file!")
                return render(request, self.template_name, {'form': form})

            insert = Film(name=name, description=description,
                          link=link, thumbnail=thumbnail)
            insert.save()
 ####
            task = convert_to_hls_task.delay(insert.id)

            cache.delete('films_list')
            films = Film.objects.select_related().all()
            cache.set('films_list', films, timeout=3600)
            cache.set(f"task_{insert.id}", task.id, timeout=3600)

            # Send response to frontend with the task_id and film_id
            return redirect('film_progress', film_id=insert.id)

        return render(request, self.template_name, {'form': form})

    def get(self, request):
        form = VideoForm()
        active_task = None
        for film in Film.objects.all():
            task_key = f"film_converting_{film.id}"
            active_task = cache.get(task_key)
            if active_task:
                break

        if active_task:
            # dodaj tutaj redirecta zeby nie wracalo add_video
            print("wypierdalaj")
        return render(request, self.template_name, locals())


class VideoViewer(LoginRequiredMixin, TemplateView):

    def get(self, request, id):
        request.session["video_id"] = id
        template_name = 'films/VideoViewer.html'

        film = Film.objects.get(id=id)

        form = RatingForm()

        ratings = cache.get('ratings')
        if not ratings:
            ratings = Ratings.objects.filter(film_id=id).select_related('user')
            cache.set('ratings', ratings, timeout=3600)

        return render(request, template_name, {"film": film, "form": form, "ratings": ratings})

    def post(self, request, id):
        form = RatingForm(request.POST)

        if request.user.is_authenticated:

            if Ratings.objects.filter(user_id=request.user.id).select_related('user'):
                return redirect('watch', id)

            else:
                if form.is_valid():
                    comment = form.cleaned_data['comments']
                    # ustaw tu pozniej z fronta
                    rating = Ratings(rating=5, film_id=id,
                                     user_id=request.user.id, comments=comment)
                    rating.save()
                return redirect('watch', id)


@method_decorator(csrf_exempt, name='dispatch')
class VProgress(View):
    def post(self, request, *args, **kwargs):
        try:
            user_id = request.user.id
            video_id = request.session["video_id"]

            data = json.loads(request.body)

            progress_time = data.get('currentTime')
            if progress_time is None:
                return JsonResponse({'error': 'No progress_time provided'}, status=400)
            if user_id is None:
                return None
            else:
                video_progress, created = VideoProgress.objects.update_or_create(
                    film_id=video_id, user_id=user_id, defaults={
                        'last_watched': progress_time}
                )

            return JsonResponse({'status': 'success', 'progress_time': progress_time})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class FilmProgressView(TemplateView):
    template_name = 'films/film_progress.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Przekazanie film_id do template
        context['film_id'] = kwargs['film_id']
        return context
