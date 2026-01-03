from django.urls import path
from . import views

app_name = 'isdown'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/check', views.api_check, name='api_check'),
]




























