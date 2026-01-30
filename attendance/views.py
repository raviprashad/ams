from datetime import date
from calendar import monthrange
import io

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.db.models import Count, Q
from django.template.loader import get_template, render_to_string

#from xhtml2pdf import pisa

from users.models import CustomUser, TeacherProfile, StudentProfile
from academics.models import Course, Session, Semester, Subject, Holiday
from timetable.models import LectureSlot
from .models import AttendanceRecord
from .forms import DeanAttendanceFilterForm


# Ajax dynamic filters
def ajax_load_sessions(request):
    course_id = request.GET.get('course_id')
    sessions = Session.objects.filter(course_id=course_id).values('id', 'name')
    return JsonResponse(list(sessions), safe=False)

def ajax_load_semesters(request):
    session_id = request.GET.get('session_id')
    semesters = Semester.objects.filter(session_id=session_id).values('id', 'name')
    return JsonResponse(list(semesters), safe=False)


from django.utils.timezone import localdate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from timetable.models import LectureSlot
from timetable.models import ScheduledLecture
from users.models import TeacherProfile
from django.http import HttpResponseForbidden

@login_required
def teacher_today_lectures(request):
    user = request.user
    try:
        teacher = user.teacherprofile
    except TeacherProfile.DoesNotExist:
        return HttpResponseForbidden("You must be a teacher to access this view.")

    today = localdate()
    weekday = today.strftime('%A')

    # Step 1: Get all slots for today's weekday
    slots_today = LectureSlot.objects.filter(teacher=teacher, day_of_week=weekday)

    # Step 2: Auto-generate scheduled lectures if not already created
    for slot in slots_today:
        ScheduledLecture.objects.get_or_create(slot=slot, date=today)

    # Step 3: Fetch all of today's scheduled lectures
    scheduled_lectures = ScheduledLecture.objects.filter(teacher=teacher, date=today).order_by('lecture_number')

    return render(request, 'users/teacher_dashboard.html', {
        'today': today,
        'lectures': scheduled_lectures,
    })

# Attendance calendar per subject
# views.py
from calendar import monthrange
from datetime import date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from academics.models import Subject
from users.models import StudentProfile, TeacherProfile
from attendance.models import ScheduledLecture, AttendanceRecord

from academics.models import Holiday  # adjust import based on your app structure

@login_required
def attendance_calendar(request, subject_id, year=None, month=None):
    subject = get_object_or_404(Subject, id=subject_id)
    today = timezone.localdate()

    if not year or not month:
        return redirect('attendance:attendance_calendar', subject_id=subject.id, year=today.year, month=today.month)

    year, month = int(year), int(month)
    num_days = monthrange(year, month)[1]

    teacher_profile = request.user.teacherprofile
    students = StudentProfile.objects.filter(
        course=subject.course,
        session=subject.session,
        semester=subject.semester
    ).select_related('user')

    # 🟨 Fetch holidays and store in a set
    holiday_dates = set(Holiday.objects.values_list('date', flat=True))

    days = []

    for day in range(1, num_days + 1):
        current_date = date(year, month, day)
        is_weekend = current_date.weekday() >= 5  # 5 = Saturday, 6 = Sunday
        is_holiday = current_date in holiday_dates

        lectures = ScheduledLecture.objects.filter(
            date=current_date,
            slot__subject=subject,
            slot__teacher=teacher_profile
        ).select_related('slot').order_by('slot__lecture_number')

        lecture_data = []
        for lecture in lectures:
            records = AttendanceRecord.objects.filter(lecture=lecture)
            status_dict = {record.student_id: record.status for record in records}
            lecture_data.append({
                'lecture': lecture,
                'status_dict': status_dict,
            })

        days.append({
            'date': current_date,
            'lectures': lecture_data,
            'is_weekend': is_weekend,
            'is_holiday': is_holiday,
        })

    return render(request, 'attendance/attendance_calendar.html', {
        'subject': subject,
        'year': year,
        'month': month,
        'days': days,
        'students': students,
    })


    
# Mark attendance for a subject on a date
from timetable.models import ScheduledLecture  # Make sure this import works


@login_required
def mark_attendance(request, lecture_id):
    # Get the ScheduledLecture instance
    scheduled_lecture = get_object_or_404(ScheduledLecture, id=lecture_id)
    slot = scheduled_lecture.slot  # This is the LectureSlot
    subject = slot.subject
    teacher = slot.teacher.user
    lecture_date = scheduled_lecture.date

    # Get all students enrolled in the subject's course, session, and semester
    students = StudentProfile.objects.filter(
        course=subject.course,
        session=subject.session,
        semester=subject.semester
    )

    # Load existing attendance records (if any) for this lecture
    existing_records = AttendanceRecord.objects.filter(lecture=scheduled_lecture)
    attendance_dict = {record.student_id: record.status for record in existing_records}

    if request.method == 'POST':
        for student in students:
            key = f'status_{student.id}'
            status = request.POST.get(key, 'Absent')  # Default to Absent if not marked

            record, created = AttendanceRecord.objects.get_or_create(
                lecture=scheduled_lecture,
                student=student.user,
                defaults={
                    'status': status,
                    'teacher': teacher,
                    'subject': subject  # ✅ Add subject here to avoid IntegrityError
                }
            )

            if not created:
                record.status = status
                record.teacher = teacher
                record.subject = subject  # ✅ In case subject was previously missing
                record.save()

        messages.success(request, "Attendance saved successfully.")
        return redirect('attendance:attendance_calendar',
                        subject_id=subject.id,
                        year=lecture_date.year,
                        month=lecture_date.month)

    return render(request, 'attendance/mark_attendance.html', {
        'lecture': scheduled_lecture,
        'subject': subject,
        'students': students,
        'attendance_dict': attendance_dict,
        'date': lecture_date,
    })
    
# Teacher: View attendance report
@login_required
def teacher_view_attendance(request, subject_id):
    teacher = getattr(request.user, 'teacherprofile', None)
    if not teacher:
        return HttpResponseForbidden("No teacher profile.")

    subject = get_object_or_404(Subject, id=subject_id)
    if not subject.teachers.filter(id=teacher.id).exists():
        return HttpResponseForbidden("You are not assigned to this subject.")

    students = CustomUser.objects.filter(
        role='student',
        studentprofile__course=subject.course,
        studentprofile__session=subject.session,
        studentprofile__semester=subject.semester
    ).distinct()

    attendance_data = []
    for student in students:
        total = AttendanceRecord.objects.filter(student=student, subject=subject).count()
        present = AttendanceRecord.objects.filter(student=student, subject=subject, status='Present').count()
        attendance_data.append({
            'student': student,
            'present': present,
            'total': total,
            'percentage': round((present / total) * 100, 2) if total else 0,
        })

    return render(request, 'attendance/teacher_view_attendance.html', {
        'subject': subject,
        'attendance_data': attendance_data
    })


# Dean: Filter and view attendance

def dean_view_attendance(request):
    students, subjects, attendance_data = [], [], {}

    if request.method == 'POST':
        form = DeanAttendanceFilterForm(request.POST)
        if form.is_valid():
            course = form.cleaned_data['course']
            session = form.cleaned_data['session']
            semester = form.cleaned_data['semester']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            subjects = Subject.objects.filter(course=course, session=session, semester=semester)
            students = StudentProfile.objects.filter(course=course, session=session, semester=semester)

            for student in students:
                attendance_data[student.id] = {}
                for subject in subjects:
                    records = AttendanceRecord.objects.filter(
                        student=student.user,
                        subject=subject,
                        lecture__date__range=[start_date, end_date]
                    )
                    total = records.count()
                    present = records.filter(status='Present').count()
                    attendance_data[student.id][subject.name] = {
                        'present': present,
                        'total': total,
                        'percentage': round((present / total) * 100, 2) if total else 0,
                    }
    else:
        form = DeanAttendanceFilterForm()

    return render(request, 'attendance/dean_view_attendance.html', {
        'form': form,
        'students': students,
        'subjects': subjects,
        'attendance_data': attendance_data
    })

# Dean: Download PDF

def dean_download_attendance_pdf(request):
    course_id = request.GET.get('course')
    session_id = request.GET.get('session')
    semester_id = request.GET.get('semester')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not all([course_id, session_id, semester_id, start_date, end_date]):
        return HttpResponseBadRequest("Missing filters")

    course = get_object_or_404(Course, id=course_id)
    session = get_object_or_404(Session, id=session_id)
    semester = get_object_or_404(Semester, id=semester_id)
    subjects = Subject.objects.filter(course=course, session=session, semester=semester)
    students = StudentProfile.objects.filter(course=course, session=session, semester=semester)

    attendance_data = {}
    for student in students:
        attendance_data[student.id] = {}
        for subject in subjects:
            records = AttendanceRecord.objects.filter(
                student=student.user,
                subject=subject,
                lecture__date__range=[start_date, end_date]  # 🔥 FIXED THIS LINE
            )
            total = records.count()
            present = records.filter(status='Present').count()
            attendance_data[student.id][subject.name] = {
                'present': present,
                'total': total,
                'percentage': round((present / total) * 100, 2) if total else 0
            }

    html = render_to_string('attendance/pdf_dean_template.html', {
        'students': students,
        'subjects': subjects,
        'attendance_data': attendance_data,
        'filters': {
            'course': course,
            'session': session,
            'semester': semester,
            'start_date': start_date,
            'end_date': end_date,
        }
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="attendance_{course.name}_{session.name}_{semester.name}.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response

# Utility: Render PDF
def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    return HttpResponse(result.getvalue(), content_type='application/pdf') if not pdf.err else None


# Teacher: Download PDF
@login_required
def download_teacher_attendance_pdf(request, subject_id):
    user = request.user
    teacher_profile = getattr(user, 'teacherprofile', None)
    if not teacher_profile:
        return HttpResponseForbidden("No teacher profile found.")

    subject = get_object_or_404(Subject, id=subject_id)
    if not subject.teachers.filter(id=teacher_profile.id).exists():
        return HttpResponseForbidden("You are not assigned to this subject.")

    students = CustomUser.objects.filter(
        role='student',
        studentprofile__course=subject.course,
        studentprofile__session=subject.session,
        studentprofile__semester=subject.semester
    ).distinct()

    attendance_data = []
    for student in students:
        total = AttendanceRecord.objects.filter(student=student, subject=subject).count()
        present = AttendanceRecord.objects.filter(student=student, subject=subject, status='Present').count()
        attendance_data.append({
            'student': student,
            'present': present,
            'total': total,
            'percentage': round((present / total) * 100, 2) if total else 0,
        })

    return render_to_pdf('attendance/pdf_template.html', {
        'subject': subject,
        'attendance_data': attendance_data
    })

from django.shortcuts import redirect
from datetime import date

def attendance_calendar_redirect(request, subject_id):
    today = date.today()
    return redirect('attendance:attendance_calendar', subject_id=subject_id, year=today.year, month=today.month)

# for teacher to view attendance calender
from django.contrib.auth.decorators import login_required
from academics.models import Subject
from users.models import TeacherProfile
from django.shortcuts import render
import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import datetime
from academics.models import Subject, TeacherProfile

@login_required
def select_subject_for_calendar(request):
    teacher_profile = TeacherProfile.objects.get(user=request.user)
    subjects = Subject.objects.filter(teachers=teacher_profile).prefetch_related('course', 'session', 'semester')
    today = datetime.date.today()
    return render(request, 'attendance/select_subject_for_calendar.html', {
        'subjects': subjects,
        'current_year': today.year,
        'current_month': today.month,
    })
