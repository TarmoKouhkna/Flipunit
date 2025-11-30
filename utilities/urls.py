from django.urls import path
from . import views

app_name = 'utilities'

urlpatterns = [
    path('', views.index, name='index'),
    path('calculator/', views.calculator, name='calculator'),
    path('qr-code-generator/', views.qr_code_generator, name='qr_code_generator'),
    path('timezone-converter/', views.timezone_converter, name='timezone_converter'),
    path('roman-numeral-converter/', views.roman_numeral_converter, name='roman_numeral_converter'),
    path('favicon-generator/', views.favicon_generator, name='favicon_generator'),
    path('timestamp-converter/', views.timestamp_converter, name='timestamp_converter'),
    path('text-to-speech/', views.text_to_speech, name='text_to_speech'),
    path('random-number-generator/', views.random_number_generator, name='random_number_generator'),
    path('lorem-ipsum-generator/', views.lorem_ipsum_generator, name='lorem_ipsum_generator'),
    path('random-word-generator/', views.random_word_generator, name='random_word_generator'),
    path('random-name-generator/', views.random_name_generator, name='random_name_generator'),
    path('word-lottery/', views.word_lottery, name='word_lottery'),
]

