from django.urls import path
from . import views

app_name = 'pdf_tools'

urlpatterns = [
    path('', views.index, name='index'),
    path('merge/', views.pdf_merge, name='pdf_merge'),
    path('split/', views.pdf_split, name='pdf_split'),
    path('to-images/', views.pdf_to_images, name='pdf_to_images'),
    path('to-html/', views.pdf_to_html, name='pdf_to_html'),
    path('html-to-pdf/', views.html_to_pdf, name='html_to_pdf'),
    path('to-text/', views.pdf_to_text, name='pdf_to_text'),
    path('compress/', views.pdf_compress, name='pdf_compress'),
    path('rotate/', views.pdf_rotate, name='pdf_rotate'),
]

