from django.urls import path
from . import views

app_name = 'image_converter'

urlpatterns = [
    path('', views.index, name='index'),
    path('universal/', views.universal_converter, name='universal'),
    path('resize/', views.resize_image, name='resize'),
    path('rotate-flip/', views.rotate_flip_image, name='rotate_flip'),
    path('remove-exif/', views.remove_exif, name='remove_exif'),
    path('grayscale/', views.convert_grayscale, name='grayscale'),
    path('merge/', views.merge_images, name='merge'),
    path('watermark/', views.watermark_image, name='watermark'),
    path('<str:converter_type>/', views.convert_image, name='convert'),
]

