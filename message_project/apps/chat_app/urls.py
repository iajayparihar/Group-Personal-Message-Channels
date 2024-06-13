# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('group_chat/<str:group_name>/', views.group_chat, name='group_chat'),
    path('personal_chat/<str:friend_username>/', views.personal_chat, name='personal_chat'),
]
    