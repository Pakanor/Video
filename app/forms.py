from django import forms


class VideoForm(forms.Form):
    video_name = forms.CharField(label="Video name", max_length=100)
    video_description = forms.CharField(
        label="Video description", max_length=100)
    link = forms.FileField()
    thumbnail = forms.FileField()


class RegisterForm(forms.Form):
    username = forms.CharField(label="username", max_length=100)
    email = forms.EmailField(
        label="email", max_length=100)
    password = forms.CharField(
        label="password", max_length=30, widget=forms.PasswordInput())


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="email", max_length=100)
    password = forms.CharField(
        label="password", max_length=30, widget=forms.PasswordInput())


class ResetForm(forms.Form):
    password = forms.CharField(
        label="password", max_length=30, widget=forms.PasswordInput())
    re_password = forms.CharField(
        label="re-password", max_length=30, widget=forms.PasswordInput())


class EmailForm(forms.Form):
    email = forms.EmailField(
        label="email", max_length=100)


class RatingForm(forms.Form):
    comments = forms.CharField(widget=forms.Textarea(attrs={"rows": "5", 'style': 'resize:none'
                                                            }))
