from django.urls import path
from . import views

app_name = 'utilities'

urlpatterns = [
    path('', views.index, name='index'),
    path('calculator/', views.calculator, name='calculator'),
    path('pdf-tools/', views.pdf_tools, name='pdf_tools'),
    path('text-tools/', views.text_tools, name='text_tools'),
]

