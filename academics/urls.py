from django.urls import path
from . import views

urlpatterns = [
    # course urls
    path('add_course/', views.add_course, name='add_course'),
    path('view_courses/', views.view_courses, name='view_courses'),
    path('edit_course/<int:course_id>/', views.edit_course, name='edit_course'),
    path('delete_course/<int:course_id>/', views.delete_course, name='delete_course'),

    # session urls
    path('add_session/', views.add_session, name='add_session'),
    path('view_sessions/', views.view_sessions, name='view_sessions'),
    path('edit_session/<int:session_id>/', views.edit_session, name='edit_session'),
    path('delete_session/<int:session_id>/', views.delete_session, name='delete_session'),

    # semester urls
    path('add_semester/', views.add_semester, name='add_semester'),
    path('view_semesters/', views.view_semesters, name='view_semesters'),
    path('edit_semester/<int:semester_id>/', views.edit_semester, name='edit_semester'),
    path('delete_semester/<int:semester_id>/', views.delete_semester, name='delete_semester'),

    # subject urls
    path('add_subject/', views.add_subject, name='add_subject'),
    path('view_subjects/', views.view_subjects, name='view_subjects'),
    path('edit_subject/<int:subject_id>/', views.edit_subject, name='edit_subject'),
    path('delete_subject/<int:subject_id>/', views.delete_subject, name='delete_subject'),

    # holidays
    path('holidays/', views.holiday_list, name='holiday_list'),
    path('holidays/add/', views.add_holiday, name='add_holiday'),
    path('holidays/edit/<int:holiday_id>/', views.edit_holiday, name='edit_holiday'),
    path('holidays/delete/<int:holiday_id>/', views.delete_holiday, name='delete_holiday'),

    # sections
    path('add_section/', views.add_section, name='add_section'),
    path('view_sections/', views.view_sections, name='view_sections'),
    path('edit_section/<int:section_id>/', views.edit_section, name='edit_section'),
    path('delete_section/<int:section_id>/', views.delete_section, name='delete_section'),

    # groups
    path('add_group/', views.add_group, name='add_group'),
    path('view_groups/', views.view_groups, name='view_groups'),
    path('edit_group/<int:group_id>/', views.edit_group, name='edit_group'),
    path('delete_group/<int:group_id>/', views.delete_group, name='delete_group'),
]
