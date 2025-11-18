from django.urls import path
from . import views

app_name = 'media_converter'

urlpatterns = [
    path('', views.index, name='index'),
    path('youtube-to-mp3/', views.youtube_to_mp3, name='youtube_to_mp3'),
    path('mp4-to-mp3/', views.mp4_to_mp3, name='mp4_to_mp3'),
    path('audio-converter/', views.audio_converter, name='audio_converter'),
    path('video-to-gif/', views.video_to_gif, name='video_to_gif'),
    path('video-converter/', views.video_converter, name='video_converter'),
]

