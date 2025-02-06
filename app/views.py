from django.shortcuts import render
from django.views.generic import TemplateView
from .models import Film, User, Ratings, VideoProgress
from .forms import VideoForm, RegisterForm, LoginForm, ResetForm, EmailForm, ResetForm, RatingForm
from django.http import HttpResponseRedirect
from django.shortcuts import render
from .python_functions import check_img
from django.core.mail import send_mail
from django.conf import settings
from .tokens import account_activation_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.hashers import check_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit

from django.test import TestCase

#            A function to create activation/restart password and then sending in to a provided email


def token(request, insert, email, title, message, what_type):
    token = account_activation_token.make_token(insert)
    uid = urlsafe_base64_encode(force_bytes(insert.pk))
    activation_link = f"{request.scheme}://{request.get_host()}/{what_type}/{uid}/{token}/"
    send_mail(f'{title}',  f"{message}: {activation_link}",
              settings.EMAIL_HOST_USER, [email])

    #####################


class Register(TemplateView):  # Register class
    template_name = 'register.html'

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user_exist = User.objects.filter(username=username)
                email_exist = User.objects.filter(email=email)
                validation = validate_password(password)
                if user_exist.exists() is False and email_exist.exists() is False:
                    if validation is None:
                        insert = User.objects.create_user(username=username,
                                                          password=password, email=email)
                        # Turning it zero so firstly the user has to click the activation link
                        insert.is_active = 0
                        insert.save()
                        token(request, insert, email, 'activation',
                              'activate your account', 'activate')

                        return render(request, 'email_verification.html')
                else:
                    raise Exception("Login or email already in use")

            except (ValidationError) as e:
                messages.add_message(request, messages.ERROR, e)
            except Exception as e:
                messages.add_message(
                    request, messages.ERROR, e)

        return render(request, self.template_name, locals())

    def get(self, request):
        # if user is logged in (the session exist in cache then redirect to the main page)
        if request.user.is_authenticated:
            return redirect('start')
        form = RegisterForm()
        return render(request, self.template_name, locals())


class Login(TemplateView):
    template_name = 'login.html'

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
        try:

            user = User.objects.get(email=email)

            active = user.is_active
            if not active:
                raise Exception("f{user.username} not active")
            password_db = user.password

            if not check_password(password, password_db):
                raise Exception("Wrong password or email")
            login(request, user)
            request.session.set_expiry(20)
            if user.is_superuser:
                return redirect('add_video')
            return redirect('start')
        except User.DoesNotExist:
            messages.add_message(
                request, messages.ERROR, "nie istnieje taki email")
            return render(request, self.template_name, locals())

        except (Exception) as e:
            messages.add_message(
                request, messages.ERROR, e)
            return render(request, self.template_name, locals())

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('start')
        form = LoginForm()

        return render(request, self.template_name, locals())

    def logout_view(request):
        logout(request)
        return redirect('/login')


class EmailForPasswordChange(TemplateView):
    template_name = "email_for_password_change.html"

    def post(self, request):
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
            token(request, user, email, "reset",
                  "reset ypur password:", 'reset')
            messages.add_message(
                request, messages.SUCCESS, f"succesfuly send to {email}")

            return render(request, self.template_name, locals())

        except (ValidationError, Exception, ValueError, User.DoesNotExist) as e:
            messages.add_message(request, messages.ERROR, e)
            return render(request, self.template_name, locals())

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('start')
        form = EmailForm()
        return render(request, self.template_name, locals())


class ChangePassword(TemplateView):
    def post(self, request, uidb64, token):
        form = ResetForm(request.POST)
        if form.is_valid():
            try:
                password = form.cleaned_data['password']
                re_password = form.cleaned_data['re_password']
                validation = validate_password(password)
                if password != re_password:
                    raise Exception("passwords not matching")
                else:
                    uid = force_str(urlsafe_base64_decode(uidb64))
                    user = User.objects.get(id=uid)
                    user.set_password(password)
                    user.save()
                    return redirect('login')

            except Exception as e:
                messages.add_message(request, messages.ERROR, e)

            except ValidationError as e:
                messages.add_message(request, messages.ERROR, e)

            except User.DoesNotExist as e:
                messages.add_message(request, messages.ERROR, e)

        return render(request, 'reset_password.html', locals())

    def get(self, request, uidb64, token):
        form = ResetForm()

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            user = None
        if user is not None and account_activation_token.check_token(user, token):

            user.save()
            return render(request, 'reset_password.html', locals())
        else:

            messages.add_message(request, messages.ERROR,
                                 "bad token or expired")
            return render(request, 'register.html')


class TokenValidation(TemplateView):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            user = None
        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            messages.add_message(request, messages.SUCCESS,
                                 "succes now log in!")
            return redirect('login')
        else:
            messages.add_message(
                request, messages.ERROR, "bad token or expired")

            return render(request, 'register.html')


class startView(TemplateView):
    template_name_logged = 'startLogged.html'
    template_name_notlogged = 'start_notLogged.html'

    def get(self, request):
        if request.user.is_authenticated:
            form = RatingForm()
            all = cache.get('films_list')
            if not all:
                all = Film.objects.all()
                cache.set('films_list', all, timeout=3600)
            return render(request, self.template_name_logged, locals())
        else:
            all = Film.objects.all()
            ratings = Ratings.objects.all()

            return render(request, self.template_name_notlogged, locals())


class Add_Video(UserPassesTestMixin, TemplateView):
    template_name = 'add_films.html'

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
                return render(request, self.template_name, locals())
            if not check_img.check_img(thumbnail):
                messages.add_message(request, messages.ERROR, "add an image!")
                return render(request, self.template_name, locals())

            else:
                insert = Film(name=name, description=description,
                              link=link, thumbnail=thumbnail)
                insert.save()
                lid = insert.id
                cache.delete('films_list')
                films = Film.objects.all()
                cache.set('films_list', films, timeout=3600)
                return HttpResponseRedirect(f"watch/{lid}")

        else:
            return render(request, self.template_name, locals())

    def get(self, request):
        form = VideoForm()
        return render(request, self.template_name, locals())


class VideoViewer(LoginRequiredMixin, TemplateView):

    def get(self, request, id):
        request.session["video_id"] = id
        template_name = 'VideoViewer.html'

        all = Film.objects.filter(id=id)

        form = RatingForm()

        ratings = cache.get('ratings')
        if not ratings:
            ratings = Ratings.objects.filter(film_id=id)
            cache.set('ratings', ratings, timeout=3600)

        return render(request, template_name, locals())

    def post(self, request, id):
        form = RatingForm(request.POST)

        if request.user.is_authenticated:

            if Ratings.objects.filter(user_id=request.user.id):
                return redirect('watch', id)

            else:
                if form.is_valid():
                    comment = form.cleaned_data['comments']
                    rating = Ratings(rating=5, film_id=18,
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
