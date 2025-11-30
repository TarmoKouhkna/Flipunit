from django.urls import path
from . import views

app_name = 'developer_converter'

urlpatterns = [
    path('', views.index, name='index'),
    path('minify/', views.minify_code, name='minify'),
    path('unminify/', views.unminify_code, name='unminify'),
    path('csv-to-json/', views.csv_to_json, name='csv_to_json'),
    path('json-to-csv/', views.json_to_csv, name='json_to_csv'),
    path('sql-formatter/', views.sql_formatter, name='sql_formatter'),
    path('css-scss/', views.css_scss, name='css_scss'),
    path('regex-tester/', views.regex_tester, name='regex_tester'),
    path('jwt-decoder/', views.jwt_decoder, name='jwt_decoder'),
    path('url-encoder/', views.url_encoder, name='url_encoder'),
    path('hash-generator/', views.hash_generator, name='hash_generator'),
]

