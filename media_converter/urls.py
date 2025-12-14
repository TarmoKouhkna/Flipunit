from django.urls import path
from . import views

app_name = 'media_converter'

urlpatterns = [
    path('', views.index, name='index'),
    path('mp4-to-mp3/', views.mp4_to_mp3, name='mp4_to_mp3'),
    path('audio-converter/', views.audio_converter, name='audio_converter'),
    path('audio-splitter/', views.audio_splitter, name='audio_splitter'),
    path('audio-merge/', views.audio_merge, name='audio_merge'),
    path('reduce-noise/', views.reduce_noise, name='reduce_noise'),
    path('video-to-gif/', views.video_to_gif, name='video_to_gif'),
    path('video-converter/', views.video_converter, name='video_converter'),
    path('video-compressor/', views.video_compressor, name='video_compressor'),
    path('mute-video/', views.mute_video, name='mute_video'),
    path('video-merge/', views.video_merge, name='video_merge'),
    path('video-preview/', views.video_preview, name='video_preview'),
]

