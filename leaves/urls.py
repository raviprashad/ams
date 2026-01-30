from django.urls import path
from . import views


urlpatterns = [
    path('apply/', views.apply_leave, name='apply_leave'),
    path('my-leaves/', views.student_leave_requests, name='student_leave_requests'),
    path('teacher/leaves/', views.teacher_leave_requests, name='teacher_leave_requests'),
    path('approve/<int:approval_id>/', views.leave_approval_action, name='leave_approval_action'),

]
