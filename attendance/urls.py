from django.urls import path
from . import views
from .views import dean_view_attendance, teacher_view_attendance

app_name = "attendance"

urlpatterns = [
    # Redirect to the current month's attendance calendar
    path('calendar/<int:subject_id>/', views.attendance_calendar, name='attendance_calendar_redirect'),
    path('calendar/<int:subject_id>/<int:year>/<int:month>/', views.attendance_calendar, name='attendance_calendar'),
    # Mark attendance by lecture (past/present/future)
    path('mark/lecture/<int:lecture_id>/', views.mark_attendance, name='mark_attendance'),

    # Dean: view overall attendance
    path('dean/view-attendance/', dean_view_attendance, name='dean_view_attendance'),

    # Dean: download attendance as PDF
    path('dean/download-attendance-pdf/', views.dean_download_attendance_pdf, name='dean_download_attendance_pdf'),

    # Teacher: view attendance for a subject
    path('teacher/view-attendance/<int:subject_id>/', teacher_view_attendance, name='teacher_view_attendance'),

    # Teacher: download their attendance for a subject
    path('download-attendance/<int:subject_id>/', views.download_teacher_attendance_pdf, name='download_teacher_attendance_pdf'),

    # AJAX for dependent dropdowns
    path('ajax/load-sessions/', views.ajax_load_sessions, name='ajax_load_sessions'),
    path('ajax/load-semesters/', views.ajax_load_semesters, name='ajax_load_semesters'),

    path('teacher/today-lectures/', views.teacher_today_lectures, name='teacher_today_lectures'),
    # attendance/urls.py
    path('calendar/select/', views.select_subject_for_calendar, name='select_subject_for_calendar')

]
