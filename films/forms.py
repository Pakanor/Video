from django import forms


class VideoForm(forms.Form):
    video_name = forms.CharField(label="Video name", max_length=100)
    video_description = forms.CharField(
        label="Video description", max_length=100)
    link = forms.FileField()
    thumbnail = forms.FileField()


class RatingForm(forms.Form):
    comments = forms.CharField(widget=forms.Textarea(attrs={"rows": "5", 'style': 'resize:none'
                                                            }))
