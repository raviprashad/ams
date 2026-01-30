from django.urls import path
from . import views

urlpatterns = [
    path('announce/', views.create_message, name='announce_message'),
    path('list/', views.message_list, name='message_list'),
    path('detail/<int:pk>/', views.message_detail, name='message_detail'),
]
