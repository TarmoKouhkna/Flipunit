from django.urls import path
from . import views

app_name = 'utilities'

urlpatterns = [
    path('', views.index, name='index'),
    path('calculator/', views.calculator, name='calculator'),
    path('pdf-tools/', views.pdf_tools, name='pdf_tools'),
    path('pdf-tools/merge/', views.pdf_merge, name='pdf_merge'),
    path('pdf-tools/split/', views.pdf_split, name='pdf_split'),
    path('pdf-tools/to-images/', views.pdf_to_images, name='pdf_to_images'),
    path('text-tools/', views.text_tools, name='text_tools'),
    path('color-converter/', views.color_converter, name='color_converter'),
    path('qr-code-generator/', views.qr_code_generator, name='qr_code_generator'),
    path('timezone-converter/', views.timezone_converter, name='timezone_converter'),
    path('roman-numeral-converter/', views.roman_numeral_converter, name='roman_numeral_converter'),
    path('favicon-generator/', views.favicon_generator, name='favicon_generator'),
]

