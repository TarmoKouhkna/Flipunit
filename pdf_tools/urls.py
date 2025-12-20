from django.urls import path
from . import views

app_name = 'pdf_tools'

urlpatterns = [
    path('', views.index, name='index'),
    path('universal/', views.universal_converter, name='universal'),
    path('merge/', views.pdf_merge, name='pdf_merge'),
    path('split/', views.pdf_split, name='pdf_split'),
    path('to-images/', views.pdf_to_images, name='pdf_to_images'),
    path('to-html/', views.pdf_to_html, name='pdf_to_html'),
    path('html-to-pdf/', views.html_to_pdf, name='html_to_pdf'),
    path('to-text/', views.pdf_to_text, name='pdf_to_text'),
    path('compress/', views.pdf_compress, name='pdf_compress'),
    path('rotate/', views.pdf_rotate, name='pdf_rotate'),
    path('ocr/', views.pdf_ocr, name='pdf_ocr'),
    path('remove-metadata/', views.pdf_remove_metadata, name='pdf_remove_metadata'),
    path('to-flipbook/', views.pdf_to_flipbook, name='pdf_to_flipbook'),
]

