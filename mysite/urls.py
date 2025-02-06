
from django.contrib import admin
from django.urls import path
from app.views import *
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('start', startView.as_view(), name='start'),
    path('watch/<int:id>', VideoViewer.as_view(), name='watch'),
    path('register', Register.as_view(), name='register'),
    path('activate/<uidb64>/<token>/',
         TokenValidation.as_view(), name='activate'),
    path('login', Login.as_view(), name='login'),
    path('request_reset', EmailForPasswordChange.as_view(), name="email_req"),
    path('reset/<uidb64>/<token>/',
         ChangePassword.as_view(), name='change_password'),
    path('logout/', Login.logout_view, name='logout'),
    path("add_video", Add_Video.as_view(), name='add_video'),
    path('watch/save-video-progress/',
         VProgress.as_view(), name='track_progress'),







]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
