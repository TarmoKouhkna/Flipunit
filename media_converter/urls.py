from django.urls import path
from . import views

app_name = 'media_converter'

urlpatterns = [
    path('', views.index, name='index'),
    path('youtube-to-mp3/', views.youtube_to_mp3, name='youtube_to_mp3'),
]

