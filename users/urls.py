from django.urls import path
from .views import (
    register, CustomLoginView, redirect_user,
    dean_dashboard, teacher_dashboard, student_dashboard,
    manage_students, add_student, delete_student, 
    student_dashboard, student_attendance_view, bulk_add_students,
    promote_students, add_teacher, view_teachers, edit_student,
    edit_teacher, delete_teacher, toggle_student_status
)
from django.contrib.auth.views import LogoutView

from .views import view_attendance_history
from .views import ajax_load_sessions, ajax_load_semesters,get_students_ajax,ajax_load_subjects

from .views import manage_student_leaves, forward_leave_to_teachers, unforward_leave_request

urlpatterns = [
    path('register/', register, name='register'),
    # path('login/', CustomLoginView.as_view(), name='login'),
    # path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    path('redirect/', redirect_user, name='redirect_user'),
    path('dean/dashboard/', dean_dashboard, name='dean_dashboard'),
    path('teacher/dashboard/', teacher_dashboard, name='teacher_dashboard'),
    path('student/dashboard/', student_dashboard, name='student_dashboard'),

    # manage students 
    path('dean/manage-students/', manage_students, name='manage_students'),
    path('dean/add-student/', add_student, name='add_student'),
    path('dean/delete-student/<int:student_id>/', delete_student, name='delete_student'),
    path('dean/edit-student/<int:student_id>/', edit_student, name='edit_student'),
    path('dean/manage-students/bulk-add/', bulk_add_students, name='bulk_add_students'),
    path('dean/manage-students/promote/', promote_students, name='promote_students'),
    path('student/attendance/<int:subject_id>/', student_attendance_view, name='student_attendance_view'),

    # manage teachers
    path('dean/add-teacher/', add_teacher, name='add_teacher'),
    path('dean/view-teachers/', view_teachers, name='view_teachers'),
    path('dean/teachers/edit/<int:teacher_id>/', edit_teacher, name='edit_teacher'),
    path('dean/teachers/delete/<int:teacher_id>/', delete_teacher, name='delete_teacher'),

    # toggle student active/inactive
    path('students/toggle/<int:student_id>/', toggle_student_status, name='toggle_student_status'),

    # View attendance history
    path('dean/attendance-history/', view_attendance_history, name='view_attendance_history'),
    path('ajax/load-sessions/', ajax_load_sessions, name='ajax_load_sessions'),
    path('ajax/load-semesters/', ajax_load_semesters, name='ajax_load_semesters'),
    path('ajax/get-students/<int:course_id>/<int:session_id>/<int:semester_id>/', get_students_ajax, name='get_students_ajax'),
    path('ajax/get-subjects/', ajax_load_subjects, name='ajax_load_subjects'),

    path('dean/manage-leaves/', manage_student_leaves, name='manage_student_leaves'),
    path('dean/forward-leave/<int:leave_id>/',forward_leave_to_teachers, name='forward_leave_to_teachers'),
    path('unforward/<int:leave_id>/', unforward_leave_request, name='unforward_leave'),

    #manage students 
    path('ajax/load-sessions/', ajax_load_sessions, name='ajax_load_sessions'),
    path('ajax/load-semesters/', ajax_load_semesters, name='ajax_load_semesters'),

]





