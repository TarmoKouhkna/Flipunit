from django.urls import path
from . import views

app_name = 'color_picker'

urlpatterns = [
    path('', views.index, name='index'),
    path('picker/', views.color_picker, name='picker'),
    path('from-image/', views.pick_from_image, name='from_image'),
]

