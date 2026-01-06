from django.urls import path
from . import views

app_name = 'text_converter'

urlpatterns = [
    path('', views.index, name='index'),
    path('uppercase-lowercase/', views.uppercase_lowercase, name='uppercase_lowercase'),
    path('camelcase-snakecase/', views.camelcase_snakecase, name='camelcase_snakecase'),
    path('remove-special/', views.remove_special_characters, name='remove_special'),
    path('remove-duplicates/', views.remove_duplicate_lines, name='remove_duplicates'),
    path('sort-lines/', views.sort_lines, name='sort_lines'),
    path('json-xml/', views.json_xml, name='json_xml'),
    path('json-yaml/', views.json_yaml, name='json_yaml'),
    path('html-markdown/', views.html_markdown, name='html_markdown'),
    path('text-base64/', views.text_base64, name='text_base64'),
    path('word-counter/', views.word_counter, name='word_counter'),
    path('audio-transcription/', views.audio_transcription, name='audio_transcription'),
    path('audio-transcription/download-docx/', views.download_transcription_docx, name='download_transcription_docx'),
]

