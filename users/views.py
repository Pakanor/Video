from django.shortcuts import render
from django.views.generic import TemplateView
from .models import User
from .forms import RegisterForm, LoginForm, ResetForm, EmailForm, ResetForm
from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.hashers import check_password
from django.contrib.auth import login
from django.contrib.auth import logout
import json
from .exceptions import *
from .tokens import *


def token(request, insert, email, title, message, what_type):
    token = account_activation_token.make_token(insert)
    uid = urlsafe_base64_encode(force_bytes(insert.pk))
    activation_link = f"{request.scheme}://{request.get_host()}/{what_type}/{uid}/{token}/"
    send_mail(f'{title}',  f"{message}: {activation_link}",
              settings.EMAIL_HOST_USER, [email])

    #####################


class Register(TemplateView):
    template_name = 'users/register.html'

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            re_password = form.cleaned_data['re_password']

            try:
                user_exist = User.objects.filter(username=username)
                email_exist = User.objects.filter(email=email)
                validation = custom_validate_password(password)
                if user_exist.exists() or email_exist.exists():
                    raise Login_or_email_in_use
                if validation is None:
                    insert = User.objects.create_user(username=username,
                                                      password=password, email=email)
                    # Turning it zero so firstly the user has to click the activation link
                    insert.is_active = 0
                    insert.save()
                    token(request, insert, email, 'activation',
                          'activate your account', 'activate')

                    return render(request, 'users/email_verification.html')

            except (WeakPasswordError, Login_or_email_in_use) as e:
                messages.add_message(request, messages.ERROR, str(e))

        return render(request, self.template_name, locals())

    def get(self, request):
        # if user is logged in (the session exist in cache then redirect to the main page)
        if request.user.is_authenticated:
            return redirect('start')
        form = RegisterForm()
        return render(request, self.template_name, locals())


class Login(TemplateView):
    template_name = 'users/login.html'

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
        try:
            user = User.objects.get(email=email)

            active = user.is_active
            if not active:
                raise Exception(f"{user.username} not active")
            password_db = user.password

            if not check_password(password, password_db):
                raise Exception("Wrong password or email")
            login(request, user)
            request.session.set_expiry(1800)
            if user.is_superuser:
                return redirect('add_video')
            return redirect('start')

        except (Exception) as e:
            messages.add_message(
                request, messages.ERROR, str(e))
            return render(request, self.template_name, locals())
        except User.DoesNotExist:
            messages.add_message(
                request, messages.ERROR, "nie istnieje taki email")
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
    template_name = "users/email_for_password_change.html"

    def post(self, request):
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
            token(request, user, email, "reset",
                  "Reset your password:", 'reset')
            messages.add_message(
                request, messages.SUCCESS, "If this email exists in our system, we will send you password reset instructions."
            )

            return render(request, self.template_name, locals())

        except User.DoesNotExist:
            messages.add_message(
                request, messages.SUCCESS, "If this email exists in our system, we will send you password reset instructions.")
            return render(request, self.template_name, locals())

        except (ValidationError, Exception, ValueError, User.DoesNotExist) as e:
            messages.add_message(request, messages.ERROR, str(e))
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
                validation = custom_validate_password(password)
                if password != re_password:
                    raise Exception("passwords not matching")
                else:
                    uid = force_str(urlsafe_base64_decode(uidb64))
                    user = User.objects.get(id=uid)
                    user.set_password(password)
                    user.save()
                    return redirect('login')

            except (CustomValidationErrorPassword, Exception) as e:
                messages.add_message(request, messages.ERROR, str(e))

            except User.DoesNotExist:
                messages.add_message(
                    request, messages.SUCCESS, "If this email exists in our system, we will send you password reset instructions.")
                return render(request, self.template_name, locals())

        return render(request, 'users/reset_password.html', locals())

    def get(self, request, uidb64, token):
        form = ResetForm()

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            user = None
        if user is not None and account_activation_token.check_token(user, token):

            user.save()
            return render(request, 'users/reset_password.html', locals())
        else:

            messages.add_message(request, messages.ERROR,
                                 "bad token or expired")
            return render(request, 'users/register.html')


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

            return render(request, 'users/register.html')
