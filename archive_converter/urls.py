from django.urls import path
from . import views

app_name = 'archive_converter'

urlpatterns = [
    path('', views.index, name='index'),
    path('rar-to-zip/', views.rar_to_zip, name='rar_to_zip'),
    path('zip-to-7z/', views.zip_to_7z, name='zip_to_7z'),
    path('7z-to-zip/', views.sevenz_to_zip, name='7z_to_zip'),
    path('targz-to-zip/', views.targz_to_zip, name='targz_to_zip'),
    path('zip-to-targz/', views.zip_to_targz, name='zip_to_targz'),
    path('extract-iso/', views.extract_iso, name='extract_iso'),
    path('create-zip/', views.create_zip_from_files, name='create_zip'),
]

