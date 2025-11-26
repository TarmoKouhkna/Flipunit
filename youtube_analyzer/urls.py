from django.urls import path
from . import views

app_name = 'youtube_analyzer'

urlpatterns = [
    path('', views.index, name='index'),
    path('analyzer/', views.analyzer_tool, name='analyzer'),
    path('analyze/', views.analyze_video, name='analyze'),
    path('download-thumbnail/', views.download_thumbnail, name='download_thumbnail'),
]

