import random
import string
from datetime import datetime
from io import BytesIO


from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.db.models import Q, Prefetch, F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.urls import reverse
from django.views.decorators.http import require_POST


from .forms import (
    CustomUserCreationForm,
    CustomLoginForm,
    AddTeacherForm,
    EditTeacherForm,
    AddStudentForm,
    EditStudentForm,
)


from .models import CustomUser, StudentProfile, TeacherProfile, StudentProfile  
from academics.models import Course, Session, Semester, Subject
from attendance.models import AttendanceRecord
from user_messages.models import Message
from leaves.models import LeaveRequest, LeaveApproval



#from xhtml2pdf import pisa
#from openpyxl import Workbook
#import openpyxl  

from django.utils import timezone
from timetable.models import LectureSlot


# to load sessions based on course
@login_required
def ajax_load_sessions(request):
    course_id = request.GET.get('course_id')
    sessions = Session.objects.filter(course_id=course_id).values('id', 'name')
    return JsonResponse({'sessions': list(sessions)})

# to load semesters based on course and session
@login_required
def ajax_load_semesters(request):
    course_id = request.GET.get('course_id')
    session_id = request.GET.get('session_id')
    semesters = Semester.objects.filter(
        course_id=course_id,
        session_id=session_id
    ).values('id', 'name')
    return JsonResponse({'semesters': list(semesters)})




def get_students_ajax(request, course_id, session_id, semester_id):
    filters = Q()
    if course_id:
        filters &= Q(course_id=course_id)
    if session_id:
        filters &= Q(session_id=session_id)
    if semester_id:
        filters &= Q(semester_id=semester_id)

    students = StudentProfile.objects.filter(filters).select_related('user')

    student_data = [
        {
            'id': student.id,
            'name': f"{student.user.first_name} {student.user.last_name}"
        }
        for student in students
    ]
    return JsonResponse({'students': student_data})

@login_required
def ajax_load_subjects(request):
    semester_id = request.GET.get('semester_id')
    subjects = Subject.objects.filter(semester_id=semester_id).values('id', 'name')
    return JsonResponse({'subjects': list(subjects)})


User = get_user_model()

def generate_random_password(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def register(request):
    courses = Course.objects.all()
    sessions = Session.objects.all()
    semesters = Semester.objects.all()

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            role = form.cleaned_data.get('role')
            user.role = role
            user.save()

            if role == 'teacher':
                TeacherProfile.objects.create(user=user)

            elif role == 'student':
                course_id = request.POST.get('course')
                session_id = request.POST.get('session')
                semester_id = request.POST.get('semester')

                if course_id and session_id and semester_id:
                    student_profile = StudentProfile.objects.create(
                        user=user,
                        course_id=course_id,
                        session_id=session_id,
                        semester_id=semester_id
                    )
                    matching_subjects = Subject.objects.filter(
                        course_id=course_id,
                        session_id=session_id,
                        semester_id=semester_id
                    )
                    Subject.objects.filter(course=..., session=..., semester=...)

                else:
                    messages.error(request, "All student fields must be filled.")
                    return render(request, 'users/register.html', {
                        'form': form,
                        'courses': courses,
                        'sessions': sessions,
                        'semesters': semesters,
                    })

            messages.success(request, "Registration successful. Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {
        'form': form,
        'courses': courses,
        'sessions': sessions,
        'semesters': semesters,
    })


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    authentication_form = CustomLoginForm

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return redirect('redirect_user')


@login_required
def redirect_user(request):
    user = request.user
    if user.role == 'dean':
        return redirect('dean_dashboard')
    elif user.role == 'teacher':
        return redirect('teacher_dashboard')
    elif user.role == 'student':
        return redirect('student_dashboard')
    else:
        return redirect('login')

from django.db.models import Prefetch
from timetable.utils import generate_today_scheduled_lectures

#teacher
from django.utils import timezone
from timetable.models import LectureSlot  # or your actual model path
from users.models import TeacherProfile


from django.utils import timezone
from timetable.models import LectureSlot
from timetable.models import ScheduledLecture
from users.models import TeacherProfile
 # if messages exist


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from timetable.models import ScheduledLecture, LectureSlot
from users.models import TeacherProfile


@login_required
def teacher_dashboard(request):
    try:
        teacher_profile = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        return render(request, 'users/error.html', {
            'message': "Teacher profile not found. Please contact admin."
        })

    today = timezone.localdate()
    weekday = today.strftime('%A')

    # Auto-create today's lectures for this teacher (excluding substitutions)
    today_slots = LectureSlot.objects.filter(day_of_week=weekday, teacher=teacher_profile)
    for slot in today_slots:
        ScheduledLecture.objects.get_or_create(slot=slot, date=today)

    # Fetch lectures where teacher is original or substitute
    scheduled_lectures = ScheduledLecture.objects.filter(
        Q(slot__teacher=teacher_profile) | Q(substitute_teacher=teacher_profile),
        date__lte=today
    ).select_related('slot__subject', 'slot__teacher', 'substitute_teacher')

    # Partition and annotate
    todays_lectures = []
    other_lectures = []

    for lec in scheduled_lectures:
        # Add flags for easy template logic
        lec.is_original = lec.slot.teacher == teacher_profile
        lec.is_substitute = lec.substitute_teacher == teacher_profile

        if lec.date == today:
            todays_lectures.append(lec)
        else:
            other_lectures.append(lec)

    # Fetch messages
    messages_qs = Message.objects.filter(for_teachers=True).order_by('-created_at')

    return render(request, 'users/teacher_dashboard.html', {
        'profile': teacher_profile,
        'todays_lectures': todays_lectures,
        'other_lectures': other_lectures,
        'messages': messages_qs,
    })
    
#student
@login_required
def student_dashboard(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        return render(request, 'users/error.html', {
            'message': "Student profile not found. Please contact admin."
        })

    subjects = Subject.objects.filter(
        course=student_profile.course,
        session=student_profile.session,
        semester=student_profile.semester
    )

    messages = Message.objects.filter(for_students=True).order_by('-created_at')

   
    if request.GET.get("download") == "pdf":
        template_path = 'users/pdf/student_subject_list.html'
        context = {
            'profile': student_profile,
            'subjects': subjects
        }
        template = get_template(template_path)
        html = template.render(context)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{request.user.username}_subjects.pdf"'

        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse("We had some errors generating the PDF.")
        return response

    return render(request, 'users/student_dashboard.html', {
        'profile': student_profile,
        'subjects': subjects,
        'messages': messages,  
    })

@login_required
def student_attendance_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    student = request.user

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    download = request.GET.get('download')

    attendance_records = AttendanceRecord.objects.filter(
        student=student,
        subject=subject
    )

    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            attendance_records = attendance_records.filter(lecture__date__range=(start, end))
        except ValueError:
            pass

    total_classes = attendance_records.count()
    present_classes = attendance_records.filter(status='Present').count()
    percentage = round((present_classes / total_classes) * 100, 2) if total_classes > 0 else 0

    if percentage >= 75:
        css_class = 'text-green'
    elif percentage >= 50:
        css_class = 'text-orange'
    else:
        css_class = 'text-red'

    context = {
        'subject': subject,
        'attendance_records': attendance_records.order_by('lecture__date'),
        'start_date': start_date,
        'end_date': end_date,
        'percentage': percentage,
        'total_classes': total_classes,
        'present_classes': present_classes,
        'css_class': css_class,
    }

    if download == 'pdf' and start_date and end_date:
        template = get_template('attendance/pdf_student_attendance.html')
        html = template.render(context)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="attendance_report.pdf"'

        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('Error generating PDF', status=500)
        return response

    return render(request, 'users/student_attendance_detail.html', context)


#dean
@login_required
def dean_dashboard(request):
    if request.user.role != 'dean':
        return redirect('login')
    return render(request, 'users/dean_dashboard.html')


@login_required
def add_teacher(request):
    if request.user.role != 'dean':
        return redirect('home')

    if request.method == 'POST':
        form = AddTeacherForm(request.POST, request=request)
        if form.is_valid():
            user = form.save(commit=False)
            password = generate_random_password()
            username_base = user.email.split('@')[0]
            user.username = username_base + str(random.randint(100, 999))
            user.set_password(password)
            user.role = 'teacher'
            user.school = request.user.school
            user.save()

            TeacherProfile.objects.create(user=user)

            send_mail(
                'Welcome to the Attendance System',
                f'Your account has been created.\n\nUsername: {user.username}\nPassword: {password}\nLogin here: http://127.0.0.1:8000/login/', #to be replaced by actual login page url before hosting
                'dummyemail@gmail,com',  # replace with dean's gmail
                [user.email],
                fail_silently=False,
            )

            messages.success(request, 'Teacher added successfully and login credentials emailed.')
            return redirect('view_teachers')
        else:
            messages.error(request, 'Form submission failed. Please correct the errors.')
    else:
        form = AddTeacherForm(request=request)

    return render(request, 'users/add_teacher.html', {'form': form})

@login_required
def view_teachers(request):
    if request.user.role != 'dean':
        return redirect('home')

    teachers = TeacherProfile.objects.filter(user__school=request.user.school).select_related('user')
    return render(request, 'users/view_teachers.html', {'teachers': teachers})




@login_required
def edit_teacher(request, teacher_id):
    if request.user.role != 'dean':
        return redirect('home')

    

    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    user = teacher.user

    if request.method == 'POST':
        form = EditTeacherForm(request.POST, instance=teacher, user_instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher details updated.')
            return redirect('view_teachers')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EditTeacherForm(instance=teacher, user_instance=user)

    return render(request, 'users/edit_teacher.html', {'form': form})


@login_required
def delete_teacher(request, teacher_id):
    if request.user.role != 'dean':
        return redirect('home')

    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    teacher.user.delete()  
    messages.success(request, 'Teacher deleted successfully.')
    return redirect('view_teachers')



@login_required
def manage_students(request):
    if request.user.role != 'dean':
        return redirect('home')

    courses = Course.objects.all()
    sessions = Session.objects.all()
    semesters = Semester.objects.all()

    # ✅ Preserve selected values from GET or POST (after redirect)
    selected_course = request.GET.get('course') or request.POST.get('course_id') or ''
    selected_session = request.GET.get('session') or request.POST.get('session_id') or ''
    selected_semester = request.GET.get('semester') or request.POST.get('semester_id') or ''

    # Start with all students
    students = StudentProfile.objects.all()

    # Apply filters if selected
    if selected_course:
        students = students.filter(course_id=selected_course)
    if selected_session:
        students = students.filter(session_id=selected_session)
    if selected_semester:
        students = students.filter(semester_id=selected_semester)

    # Student addition form
    form = AddStudentForm()
    if request.method == 'POST' and 'add_student' in request.POST:
        form = AddStudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student added successfully.")
            return redirect('manage_students')

    return render(request, 'users/manage_students.html', {
        'courses': courses,
        'sessions': sessions,
        'semesters': semesters,
        'selected_course': selected_course,
        'selected_session': selected_session,
        'selected_semester': selected_semester,
        'students': students,
        'form': form,
        'request': request,
    })


@login_required
def toggle_student_status(request, student_id):
    if request.user.role != 'dean':
        return redirect('home')

    student = get_object_or_404(StudentProfile, id=student_id)
    student.is_active = not student.is_active
    student.save()
    messages.success(request, f"Student {'activated' if student.is_active else 'deactivated'} successfully.")
    return redirect('manage_students')




@login_required
def add_student(request):
    if request.user.role != 'dean':
        return redirect('home')

    if request.method == 'POST':
        form = AddStudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.user.school = request.user.school
            student.user.save()
            student.save()

            generated_password = form.generated_password  

            messages.success(
                request,
                f"Student added successfully. Temporary password: {generated_password}"
            )
            return redirect('manage_students')
    else:
        form = AddStudentForm()

    return render(request, 'users/add_student.html', {'form': form})



#email the password to the user (during adding students manually)-- uncomment and replace

# @login_required
# def add_student(request):
#     if request.user.role != 'dean':
#         return redirect('home')

#     if request.method == 'POST':
#         form = AddStudentForm(request.POST)
#         if form.is_valid():
#             student = form.save(commit=False)
#             student.user.school = request.user.school
#             student.user.save()
#             student.save()

#             # Securely email the password to the student
#             subject = 'Your Student Account Details'
#             message = (
#                 f"Hi {student.user.first_name},\n\n"
#                 f"Your student account has been created successfully.\n\n"
#                 f"Username: {student.user.username}\n"
#                 f"Temporary Password: {form.generated_password}\n\n"
#                 "Please login and change your password as soon as possible."
#             )
#             recipient = [student.user.email]

#             send_mail(subject, message, settings.EMAIL_HOST_USER, recipient, fail_silently=False)

#             messages.success(request, f"Student added successfully. Credentials have been sent via email.")
#             return redirect('manage_students')
#     else:
#         form = AddStudentForm()

#     return render(request, 'users/add_student.html', {'form': form})


@login_required
def bulk_add_students(request):
    if request.method == 'POST' and request.user.role == 'dean':
        course_id = request.POST.get('course')
        session_id = request.POST.get('session')
        semester_id = request.POST.get('semester')
        excel_file = request.FILES.get('excel_file')

        if not all([course_id, session_id, semester_id, excel_file]):
            messages.error(request, "All fields are required.")
            return redirect('manage_students')

        course = Course.objects.get(id=course_id)
        session = Session.objects.get(id=session_id)
        semester = Semester.objects.get(id=semester_id)

        try:
            wb = openpyxl.load_workbook(excel_file)
            sheet = wb.active

            for i, row in enumerate(sheet.iter_rows(min_row=2), start=2): #skipping headers
                email = str(row[0].value).strip()
                first_name = str(row[1].value).strip()
                last_name = str(row[2].value).strip()
                enrollment_number = str(row[3].value).strip()

                if CustomUser.objects.filter(username=email).exists():
                    continue  #skipping duplicates 

                password = CustomUser.objects.make_random_password()
                user = CustomUser.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                    role='student',
                    school=request.user.school
                )

                StudentProfile.objects.create(
                    user=user,
                    course=course,
                    session=session,
                    semester=semester,
                    enrollment_number=enrollment_number
                )

                # for password email - during bulk add
                send_mail(
                    subject="Your Student Account Credentials",
                    message=(
                        f"Hello {first_name},\n\n"
                        f"Your student account has been created.\n"
                        f"Username: {email}\nTemporary Password: {password}\n"
                        "Please change your password after your first login.\n\nThank you."
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )

            messages.success(request, "Students added and notified successfully.")

        except Exception as e:
            messages.error(request, f"Error reading Excel file: {str(e)}")

        return redirect('manage_students')

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from academics.models import Semester  # Adjust import based on your app name
from users.models import StudentProfile  # Adjust import based on your app

@login_required
def promote_students(request):
    if request.method == "POST":
        course_id = request.POST.get("course_id")
        session_id = request.POST.get("session_id")
        semester_id = request.POST.get("semester_id")
        selected_ids = request.POST.getlist("selected_students[]")

        if not semester_id:
            messages.error(request, "Please select a semester before promoting students.")
            return redirect(f"/users/dean/manage-students/?course={course_id}&session={session_id}&semester={semester_id}")

        if not selected_ids:
            messages.error(request, "No students selected for promotion.")
            return redirect(f"/users/dean/manage-students/?course={course_id}&session={session_id}&semester={semester_id}")

        try:
            semester_id = int(semester_id)
        except ValueError:
            messages.error(request, "Invalid semester selected.")
            return redirect(f"/users/dean/manage-students/?course={course_id}&session={session_id}&semester={semester_id}")

        current_semester = get_object_or_404(Semester, id=semester_id)

        # ✅ Only promote selected students
        students = StudentProfile.objects.filter(id__in=selected_ids)

        try:
            next_semester = Semester.objects.get(
                course=current_semester.course,
                session=current_semester.session,
                order=current_semester.order + 1
            )
        except Semester.DoesNotExist:
            messages.warning(request, "No next semester found for promotion.")
            return redirect(f"/users/dean/manage-students/?course={course_id}&session={session_id}&semester={semester_id}")

        promoted_count = 0
        for student in students:
            student.semester = next_semester
            student.save()
            promoted_count += 1

        messages.success(request, f"{promoted_count} student(s) promoted to {next_semester.name}.")
        return redirect(f"/users/dean/manage-students/?course={course_id}&session={session_id}&semester={next_semester.id}")

    messages.error(request, "Invalid request method.")
    return redirect("manage_students")

@login_required
def edit_student(request, student_id):
    if request.user.role != 'dean':
        return redirect('home')

    student_profile = get_object_or_404(StudentProfile, id=student_id)
    student_user = student_profile.user

    if request.method == 'POST':
        form = EditStudentForm(request.POST, instance=student_profile, user_instance=student_user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully.')
            return redirect('manage_students')
    else:
        form = EditStudentForm(instance=student_profile, user_instance=student_user)

    return render(request, 'users/edit_student.html', {'form': form})



@login_required
def delete_student(request, student_id):
    if request.user.role != 'dean':
        messages.error(request, "You don't have permission to delete students.")
        return redirect('manage_students') 

    student = get_object_or_404(StudentProfile, id=student_id)

    # deleting associated user
    user = student.user
    student.delete()
    user.delete()

    messages.success(request, f"Student '{user.username}' deleted successfully.")
    return redirect('manage_students') 







@login_required
def view_attendance_history(request):
    courses = Course.objects.all()
    sessions = Session.objects.all()
    semesters = Semester.objects.all()
    subjects = []
    attendance_data = []
    subject = None  # <== Fixes the UnboundLocalError

    course_id = request.GET.get('course')
    session_id = request.GET.get('session')
    semester_id = request.GET.get('semester')
    subject_id = request.GET.get('subject')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    export = request.GET.get('export')

    students = StudentProfile.objects.none()

    if course_id and session_id:
        students = StudentProfile.objects.filter(
            course_id=course_id,
            session_id=session_id
        ).select_related('user')

    if semester_id:
        subjects = Subject.objects.filter(semester_id=semester_id)

    if subject_id and start_date and end_date:
        subject = get_object_or_404(Subject, id=subject_id)

        for student in students:
            total_classes = AttendanceRecord.objects.filter(
                subject=subject,
                date__range=[start_date, end_date],
                session_id=session_id,
                student=student.user
            ).values('date').distinct().count()

            present_count = AttendanceRecord.objects.filter(
                subject=subject,
                student=student.user,
                status='Present',
                date__range=[start_date, end_date],
                session_id=session_id
            ).count()

            absent_count = total_classes - present_count
            percentage = round((present_count / total_classes * 100), 2) if total_classes else 0

            attendance_data.append({
                'name': f"{student.user.first_name} {student.user.last_name}",
                'enrollment': student.enrollment_number,
                'total': total_classes,
                'present': present_count,
                'absent': absent_count,
                'percentage': percentage
            })

    # Excel Export
    if export == 'excel' and subject:
        wb = Workbook()
        ws = wb.active
        ws.title = "Attendance Report"

        ws.append(['Student', 'Enrollment', 'Total Classes', 'Present', 'Absent', 'Attendance %'])

        for row in attendance_data:
            ws.append([
                row['name'], row['enrollment'], row['total'],
                row['present'], row['absent'], row['percentage']
            ])

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=attendance_report.xlsx'
        return response

    # PDF Export
    if export == 'pdf' and subject_id and start_date and end_date:
        subject = get_object_or_404(Subject, id=subject_id)
        attendance_records = AttendanceRecord.objects.filter(
            subject=subject,
            date__range=[start_date, end_date],
            session_id=session_id
        ).order_by('date')

        total_classes = attendance_records.values('date').distinct().count()
        present_classes = attendance_records.filter(status='Present').count()
        percentage = round((present_classes / total_classes * 100), 2) if total_classes else 0

        template = get_template('attendance/pdf_student_attendance.html')
        html = template.render({
            'subject': subject,
            'start_date': start_date,
            'end_date': end_date,
            'attendance_records': attendance_records,
            'total_classes': total_classes,
            'present_classes': present_classes,
            'percentage': percentage
        })

        buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=buffer)

        if pisa_status.err:
            return HttpResponse('Error generating PDF', status=500)

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=attendance_report.pdf'
        return response

    context = {
        'courses': courses,
        'sessions': sessions,
        'semesters': semesters,
        'subjects': subjects,
        'attendance_data': attendance_data,
        'selected_course': course_id,
        'selected_session': session_id,
        'selected_semester': semester_id,
        'selected_subject': subject_id,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'academics/view_attendance_history.html', context)


@login_required
def manage_student_leaves(request):
    if not hasattr(request.user, 'deanprofile'):
        return render(request, 'users/error.html', {'message': "You are not authorized."})

    dean_school = request.user.deanprofile.school

    courses = Course.objects.filter(school=dean_school)
    sessions = Session.objects.all()
    semesters = Semester.objects.all()

    
    approvals_qs = LeaveApproval.objects.select_related('teacher')
    leaves = LeaveRequest.objects.filter(
        student__studentprofile__course__school=dean_school
    ).select_related(
        'student',
        'student__studentprofile__course',
        'student__studentprofile__session',
        'student__studentprofile__semester'
    ).prefetch_related(
        Prefetch('approvals', queryset=approvals_qs)
    )

    # filters
    course_id = request.GET.get('course')
    session_id = request.GET.get('session')
    semester_id = request.GET.get('semester')
    forwarded_filter = request.GET.get('forwarded')
    search = request.GET.get('search')

    if course_id:
        leaves = leaves.filter(student__studentprofile__course_id=course_id)
        sessions = sessions.filter(course_id=course_id)
        semesters = semesters.filter(course_id=course_id)

    if session_id:
        leaves = leaves.filter(student__studentprofile__session_id=session_id)
        semesters = semesters.filter(session_id=session_id)

    if semester_id:
        leaves = leaves.filter(student__studentprofile__semester_id=semester_id)

    if forwarded_filter == 'yes':
        leaves = leaves.filter(is_forwarded_by_dean=True)
    elif forwarded_filter == 'no':
        leaves = leaves.filter(is_forwarded_by_dean=False)

    if search:
        leaves = leaves.filter(
            Q(student__username__icontains=search) |
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search) |
            Q(student__studentprofile__course__name__icontains=search)
        )

    return render(request, 'users/dean_manage_leaves.html', {
        'pending_leaves': leaves,
        'courses': courses,
        'sessions': sessions,
        'semesters': semesters,
        'selected_course': course_id,
        'selected_session': session_id,
        'selected_semester': semester_id,
    })




@require_POST
@login_required
def forward_leave_to_teachers(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id)

    if not hasattr(request.user, 'deanprofile'):
        messages.error(request, "You are not authorized to perform this action.")
        return redirect_with_filters(request)

    if leave.is_forwarded_by_dean:
        messages.warning(request, "This leave request has already been forwarded.")
        return redirect_with_filters(request)

    try:
        student_profile = leave.student.studentprofile
        subjects = Subject.objects.filter(
            course=student_profile.course,
            semester=student_profile.semester
        ).prefetch_related('teachers')

        teachers_set = set()
        for subject in subjects:
            teachers_set.update(subject.teachers.all())

        for teacher_profile in teachers_set:
            LeaveApproval.objects.create(
                leave_request=leave,
                teacher=teacher_profile.user,
                status='pending'
            )

        leave.is_forwarded_by_dean = True
        leave.save()

        messages.success(request, "Leave successfully forwarded to teachers.")
        return redirect_with_filters(request)

    except Exception as e:
        messages.error(request, f"Failed to forward leave: {str(e)}")
        return redirect_with_filters(request)



@require_POST
@login_required
def unforward_leave_request(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id)

    if not hasattr(request.user, 'deanprofile'):
        return redirect_with_filters(request)

    if not leave.is_forwarded_by_dean:
        return redirect_with_filters(request)

    try:
        leave.approvals.all().delete()
        leave.is_forwarded_by_dean = False
        leave.status = 'pending'  
        leave.save(update_fields=['is_forwarded_by_dean', 'status'])

        messages.success(request, "Leave request has been unforwarded.")
        return redirect_with_filters(request)

    except Exception as e:
        messages.error(request, f"Unforward failed: {str(e)}")
        return redirect_with_filters(request)





def redirect_with_filters(request):
    query_string = request.META.get('QUERY_STRING', '')
    return redirect(f"{reverse('manage_student_leaves')}?{query_string}")
