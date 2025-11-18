from django.urls import path
from . import views

app_name = 'image_converter'

urlpatterns = [
    path('', views.index, name='index'),
    path('resize/', views.resize_image, name='resize'),
    path('<str:converter_type>/', views.convert_image, name='convert'),
]

