
from django.contrib import admin
from django.urls import path
from meine_app import views as app_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', app_views.login, name='login'),
    path('register/', app_views.register, name='register'),
    path('dashboard/', app_views.dashboard, name='dashboard'),
    
    path('loesche/<str:dateiname>/', app_views.loesche_aufnahme, name='loesche_aufnahme'),
    
    path('pushtotalk/', app_views.pushtotalk, name='pushtotalk'),
    
    path('api/pi/upload/', app_views.pi_api_upload, name='pi_api_upload'),
    path('api/pi/get_latest/', app_views.pi_api_get_latest, name='pi_api_get_latest'),
    path('api/website/upload/', app_views.website_audio_upload, name='website_audio_upload'),
]

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)