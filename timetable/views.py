# timetable/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from collections import defaultdict

from .forms import LectureSlotForm
from .models import LectureSlot
from academics.models import Course, Session, Semester, Subject
from users.models import TeacherProfile
from academics.models import Section, StudentGroup


# AJAX: Get sessions by course
def get_sessions(request):
    course_id = request.GET.get('course_id')
    sessions = Session.objects.filter(course_id=course_id).values('id', 'name')
    return JsonResponse({'sessions': list(sessions)})

# AJAX: Get semesters by course
def get_semesters(request):
    course_id = request.GET.get('course_id')
    semesters = Semester.objects.filter(course_id=course_id).values('id', 'name')
    return JsonResponse({'semesters': list(semesters)})


# Create/Assign a new lecture slot
def add_timetable(request):
    if request.method == 'POST':
        form = LectureSlotForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Lecture slot added successfully!")
            return redirect('add_timetable')
        else:
            messages.error(request, "There was an error. Please check the form.")
    else:
        form = LectureSlotForm()
    
    slots = LectureSlot.objects.all().order_by('day_of_week', 'lecture_number')
    context = {
        'form': form,
        'slots': slots,
    }
    return render(request, 'timetable/add_timetable.html', context)


# Delete a slot
def delete_lecture_slot(request, slot_id):
    lecture_slot = get_object_or_404(LectureSlot, id=slot_id)
    lecture_slot.delete()
    messages.success(request, "Lecture slot deleted successfully.")
    return redirect('add_timetable')


# Edit a lecture slot
def edit_lecture_slot(request, slot_id):
    slot = get_object_or_404(LectureSlot, id=slot_id)
    if request.method == 'POST':
        form = LectureSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            messages.success(request, "Lecture slot updated successfully.")
            return redirect('view_timetable')  # Can enhance to preserve filters
    else:
        form = LectureSlotForm(instance=slot)
    return render(request, 'timetable/edit_lecture_slot.html', {'form': form, 'slot': slot})


# View timetable with filters

    courses = Course.objects.all()
    sessions = Session.objects.all()
    semesters = Semester.objects.all()

    selected_course_id = request.GET.get('course')
    selected_session_id = request.GET.get('session')
    selected_semester_id = request.GET.get('semester')

    timetable = []
    timetable_dict = defaultdict(lambda: defaultdict(lambda: None))
    lecture_numbers = []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    if selected_course_id and selected_session_id and selected_semester_id:
        timetable = LectureSlot.objects.filter(
            subject__course_id=selected_course_id,
            subject__session_id=selected_session_id,
            subject__semester_id=selected_semester_id
        )

        for slot in timetable:
            timetable_dict[slot.day_of_week][slot.lecture_number] = slot

        lecture_numbers = sorted({slot.lecture_number for slot in timetable})

    return render(request, 'timetable/view_timetable.html', {
        'courses': courses,
        'sessions': sessions,
        'semesters': semesters,
        'selected_course_id': selected_course_id,
        'selected_session_id': selected_session_id,
        'selected_semester_id': selected_semester_id,
        'timetable': timetable,
        'timetable_dict': timetable_dict,
        'lecture_numbers': lecture_numbers,
        'days': days
    })

def view_timetable(request):
    courses = Course.objects.all()
    sessions = Session.objects.all()
    semesters = Semester.objects.all()

    # New optional filters:
    sections = Section.objects.all()
    groups = StudentGroup.objects.all()

    selected_course_id = request.GET.get('course')
    selected_session_id = request.GET.get('session')
    selected_semester_id = request.GET.get('semester')
    selected_section_id = request.GET.get('section')  # new
    selected_group_id = request.GET.get('group')      # new

    timetable = []
    timetable_dict = defaultdict(lambda: defaultdict(lambda: None))
    lecture_numbers = []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    if selected_course_id and selected_session_id and selected_semester_id:
        queryset = LectureSlot.objects.filter(
            subject__course_id=selected_course_id,
            subject__session_id=selected_session_id,
            subject__semester_id=selected_semester_id,
        )

        # Optional filters
        if selected_section_id:
            queryset = queryset.filter(section_id=selected_section_id)
        if selected_group_id:
            queryset = queryset.filter(group_id=selected_group_id)

        timetable = queryset

        for slot in timetable:
            timetable_dict[slot.day_of_week][slot.lecture_number] = slot

        lecture_numbers = sorted({slot.lecture_number for slot in timetable})

    return render(request, 'timetable/view_timetable.html', {
        'courses': courses,
        'sessions': sessions,
        'semesters': semesters,
        'sections': sections,
        'groups': groups,
        'selected_course_id': selected_course_id,
        'selected_session_id': selected_session_id,
        'selected_semester_id': selected_semester_id,
        'selected_section_id': selected_section_id,
        'selected_group_id': selected_group_id,
        'timetable': timetable,
        'timetable_dict': timetable_dict,
        'lecture_numbers': lecture_numbers,
        'days': days
    })

# Landing page (Dean selects to Add/View timetable)
def manage_timetable_home(request):
    return render(request, 'timetable/manage_timetable_home.html')


# views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from users.models import TeacherProfile
from timetable.models import ScheduledLecture
from django.contrib import messages
from django.db.models import Q

# timetable/views.py
from timetable.forms import AssignSubstituteForm
from django.urls import reverse

@login_required
# timetable/views.py
def assign_substitute(request, lecture_id):
    lecture = get_object_or_404(ScheduledLecture, id=lecture_id)
    original_teacher = lecture.teacher

    eligible_teachers = TeacherProfile.objects.exclude(id=original_teacher.id)

    teacher_subject_map = {
        teacher.id: Subject.objects.filter(teachers=teacher)
        for teacher in eligible_teachers
    }

    if request.method == 'POST':
        form = AssignSubstituteForm(
            request.POST,
            eligible_teachers=eligible_teachers,
            teacher_subject_map=teacher_subject_map
        )
        if form.is_valid():
            substitute_teacher = form.cleaned_data['substitute_teacher']
            substitute_subject = form.cleaned_data['substitute_subject']

            lecture.substitute_teacher = substitute_teacher
            lecture.substitute_subject = substitute_subject
            lecture.save()

            messages.success(request, "Substitute assigned successfully.")
            return redirect('teacher_dashboard')
    else:
        form = AssignSubstituteForm(
            eligible_teachers=eligible_teachers,
            teacher_subject_map=teacher_subject_map
        )

    return render(request, 'timetable/assign_substitute.html', {
        'lecture': lecture,
        'form': form
    })

from django.http import JsonResponse

@login_required
def get_subjects_for_teacher(request):
    teacher_id = request.GET.get('teacher_id')
    subjects = []
    if teacher_id:
        subjects = Subject.objects.filter(teachers__id=teacher_id).values('id', 'name')
    return JsonResponse(list(subjects), safe=False)


from django.views.decorators.http import require_POST

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from timetable.models import ScheduledLecture
from users.models import TeacherProfile

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from timetable.models import ScheduledLecture
from users.models import TeacherProfile

@login_required
def revert_substitute(request, lecture_id):
    lecture = get_object_or_404(ScheduledLecture, id=lecture_id)
    
    if lecture.slot.teacher.user != request.user:
        messages.error(request, "Not authorized to revert this substitution.")
        return redirect('teacher_dashboard')

    if request.method == 'POST':
        lecture.substitute_teacher = None
        lecture.substitute_subject = None
        lecture.teacher = lecture.slot.teacher
        lecture.subject = lecture.slot.subject
        lecture.save()
        messages.success(request, "Substitute assignment reverted.")
        return redirect('teacher_dashboard')

    return render(request, 'timetable/confirm_revert.html', {
        'lecture': lecture
    })
