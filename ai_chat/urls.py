from django.urls import path
from . import views

app_name = 'ai_chat'

urlpatterns = [
    path('', views.chat_index, name='index'),
    path('api/message', views.chat_api, name='chat_api'),
]
