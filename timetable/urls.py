from django.urls import path
from . import views

urlpatterns = [
    path('', views.manage_timetable_home, name='manage_timetable_home'),  # 👈 Dean lands here
    path('add/', views.add_timetable, name='add_timetable'),
    path('delete/<int:slot_id>/', views.delete_lecture_slot, name='delete_lecture_slot'),
    path('view/', views.view_timetable, name='view_timetable'),
    # urls.py
    path('timetable/edit/<int:slot_id>/', views.edit_lecture_slot, name='edit_lecture_slot'),
    path('get-sessions/', views.get_sessions, name='get_sessions'),
    path('get-semesters/', views.get_semesters, name='get_semesters'),
    path('assign-substitute/<int:lecture_id>/', views.assign_substitute, name='assign_substitute'),
    path('get-subjects/', views.get_subjects_for_teacher, name='get_subjects_for_teacher'),
    path('revert-substitute/<int:lecture_id>/', views.revert_substitute, name='revert_substitute'),


  
]


