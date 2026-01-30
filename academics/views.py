from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import AddSubjectForm, AddSessionForm, AddSemesterForm, AddSubjectForm, AddCourseForm, HolidayForm
from .models import Subject, Course, Session, Semester,Subject,Holiday
from django.contrib.auth.decorators import login_required
from django.contrib import messages


#course views
@login_required
def add_course(request):
    if request.user.role != 'dean':
        return redirect('home') 

    school = request.user.school 

    if request.method == 'POST':
        form = AddCourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.school = school  
            course.save()
            messages.success(request, "Course added successfully!")
            return redirect('add_course')
        else:
            messages.error(request, "Failed to add course. Please fix the errors below.")
    else:
        form = AddCourseForm()

    return render(request, 'academics/add_course.html', {'form': form})


@login_required
def edit_course(request, course_id):
    if request.user.role != 'dean':
        return redirect('home')

    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = AddCourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully.")
            return redirect('add_course')
        else:
            messages.error(request, "Failed to update course.")
    else:
        form = AddCourseForm(instance=course)

    return render(request, 'academics/edit_course.html', {'form': form, 'course': course})


@login_required
def delete_course(request, course_id):
    if request.user.role != 'dean':
        return redirect('home')

    course = get_object_or_404(Course, id=course_id)
    course.delete()
    messages.success(request, "Course deleted successfully.")
    return redirect('add_course')

@login_required
def view_courses(request):
    if request.user.role != 'dean':
        return redirect('home')

    school = request.user.school  
    courses = Course.objects.filter(school=school)
    return render(request, 'academics/view_courses.html', {'courses': courses})



#session views
@login_required
def add_session(request):
    if request.user.role != 'dean':
        return redirect('home')

    if request.method == 'POST':
        form = AddSessionForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            course = form.cleaned_data['course']
            if Session.objects.filter(name=name, course=course).exists():
                messages.error(request, "This session already exists for the selected course.")
            else:
                form.save()
                messages.success(request, "Session added successfully.")
                return redirect('add_session')
    else:
        form = AddSessionForm()
    return render(request, 'academics/add_session.html', {'form': form})


@login_required
def view_sessions(request):
    if request.user.role != 'dean':
        return redirect('home')

    school = request.user.school  
    sessions = Session.objects.filter(course__school=school)
    return render(request, 'academics/view_sessions.html', {'sessions': sessions})


@login_required
def edit_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)

    if request.method == 'POST':
        form = AddSessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, "Session updated successfully.")
            return redirect('view_sessions')
    else:
        form = AddSessionForm(instance=session)

    return render(request, 'academics/edit_session.html', {'form': form})


@login_required
def delete_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    session.delete()
    messages.success(request, "Session deleted successfully.")
    return redirect('view_sessions')

#semester views
from django.db.models import Max

@login_required
def add_semester(request):
    if request.user.role != 'dean':
        return redirect('home')

    if request.method == 'POST':
        form = AddSemesterForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            course = form.cleaned_data['course']
            session = form.cleaned_data['session']

            
            if Semester.objects.filter(name=name, course=course, session=session).exists():
                messages.error(request, "Semester already exists.")
            else:
                
                max_order = Semester.objects.filter(course=course, session=session).aggregate(
                    Max('order')
                )['order__max'] or 1    #default = 1

                semester = form.save(commit=False)
                semester.order = max_order + 1  
                semester.save()

                messages.success(request, "Semester added successfully.")
                return redirect('view_semesters')
    else:
        form = AddSemesterForm()

    return render(request, 'academics/add_semester.html', {'form': form})

@login_required
def view_semesters(request):
    if request.user.role != 'dean':
        return redirect('home')

    school = request.user.school  
    semesters = Semester.objects.filter(course__school=school).order_by('course', 'session', 'name')
    return render(request, 'academics/view_semesters.html', {'semesters': semesters})


@login_required
def edit_semester(request, semester_id):
    if request.user.role != 'dean':
        return redirect('home')

    semester = Semester.objects.get(id=semester_id)
    form = AddSemesterForm(request.POST or None, instance=semester)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Semester updated successfully.")
        return redirect('view_semesters')

    return render(request, 'academics/edit_semester.html', {'form': form})

@login_required
def delete_semester(request, semester_id):
    if request.user.role != 'dean':
        return redirect('home')

    semester = Semester.objects.get(id=semester_id)
    semester.delete()
    messages.success(request, "Semester deleted successfully.")
    return redirect('view_semesters')

#subject views

def is_dean(user):
    return hasattr(user, 'deanprofile') 

@login_required
def add_subject(request):
    if request.user.role != 'dean':
        return redirect('home')

    if request.method == 'POST':
        form = AddSubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()  
            messages.success(request, "Subject added successfully.")
            return redirect('add_subject')
    else:
        form = AddSubjectForm()

    return render(request, 'academics/add_subject.html', {'form': form})


@login_required
def view_subjects(request):
    if request.user.role != 'dean':
        return redirect('home')

    school = request.user.school  
    subjects = Subject.objects.filter(course__school=school).order_by('course', 'session', 'semester', 'name')
    return render(request, 'academics/view_subjects.html', {'subjects': subjects})


@login_required
def edit_subject(request, subject_id):
    if request.user.role != 'dean':
        return redirect('home')

    subject = Subject.objects.get(id=subject_id)
    form = AddSubjectForm(request.POST or None, instance=subject)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Subject updated successfully.")
        return redirect('view_subjects')

    return render(request, 'academics/edit_subject.html', {'form': form})

@login_required
def delete_subject(request, subject_id):
    if request.user.role != 'dean':
        return redirect('home')

    subject = Subject.objects.get(id=subject_id)
    subject.delete()
    messages.success(request, "Subject deleted successfully.")
    return redirect('view_subjects')


#holiday views
@login_required
def holiday_list(request):
    holidays = Holiday.objects.all().order_by('date')
    return render(request, 'academics/holiday_list.html', {'holidays': holidays})

@login_required
def add_holiday(request):
    if request.method == 'POST':
        form = HolidayForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('holiday_list')
    else:
        form = HolidayForm()
    return render(request, 'academics/holiday_form.html', {'form': form, 'action': 'Add'})

@login_required
def edit_holiday(request, holiday_id):
    holiday = get_object_or_404(Holiday, id=holiday_id)
    if request.method == 'POST':
        form = HolidayForm(request.POST, instance=holiday)
        if form.is_valid():
            form.save()
            return redirect('holiday_list')
    else:
        form = HolidayForm(instance=holiday)
    return render(request, 'academics/holiday_form.html', {'form': form, 'action': 'Edit'})

@login_required
def delete_holiday(request, holiday_id):
    holiday = get_object_or_404(Holiday, id=holiday_id)
    if request.method == 'POST':
        holiday.delete()
        return redirect('holiday_list')
    return render(request, 'academics/holiday_confirm_delete.html', {'holiday': holiday})

# -------------------
# Section Views
# -------------------

from .forms import AddSectionForm, AddGroupForm
from .models import Section, StudentGroup

@login_required
def add_section(request):
    if request.user.role != 'dean':
        return redirect('home')

    school = request.user.school

    if request.method == 'POST':
        form = AddSectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)
            section.school = school
            section.save()
            messages.success(request, "Section added successfully.")
            return redirect('view_sections')
        else:
            messages.error(request, "Failed to add section.")
    else:
        form = AddSectionForm()

    return render(request, 'academics/add_section.html', {'form': form})


@login_required
def view_sections(request):
    if request.user.role != 'dean':
        return redirect('home')

    school = request.user.school
    sections = Section.objects.filter(course__school=school)
    return render(request, 'academics/view_sections.html', {'sections': sections})


@login_required
def edit_section(request, section_id):
    if request.user.role != 'dean':
        return redirect('home')

    section = get_object_or_404(Section, id=section_id)
    if request.method == 'POST':
        form = AddSectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, "Section updated successfully.")
            return redirect('view_sections')
        else:
            messages.error(request, "Failed to update section.")
    else:
        form = AddSectionForm(instance=section)

    return render(request, 'academics/edit_section.html', {'form': form})


@login_required
def delete_section(request, section_id):
    if request.user.role != 'dean':
        return redirect('home')

    section = get_object_or_404(Section, id=section_id)
    section.delete()
    messages.success(request, "Section deleted successfully.")
    return redirect('view_sections')


# -------------------
# Group Views
# -------------------

@login_required
def add_group(request):
    if request.user.role != 'dean':
        return redirect('home')

    school = request.user.school

    if request.method == 'POST':
        form = AddGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.school = school
            group.save()
            messages.success(request, "Group added successfully.")
            return redirect('view_groups')
        else:
            messages.error(request, "Failed to add group.")
    else:
        form = AddGroupForm()

    return render(request, 'academics/add_group.html', {'form': form})


@login_required
def view_groups(request):
    if request.user.role != 'dean':
        return redirect('home')

    school = request.user.school
    groups = StudentGroup.objects.filter(course__school=school)
    return render(request, 'academics/view_groups.html', {'groups': groups})


@login_required
def edit_group(request, group_id):
    if request.user.role != 'dean':
        return redirect('home')

    group = get_object_or_404(StudentGroup, id=group_id)
    if request.method == 'POST':
        form = AddGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, "Group updated successfully.")
            return redirect('view_groups')
        else:
            messages.error(request, "Failed to update group.")
    else:
        form = AddGroupForm(instance=group)

    return render(request, 'academics/edit_group.html', {'form': form})


@login_required
def delete_group(request, group_id):
    if request.user.role != 'dean':
        return redirect('home')

    group = get_object_or_404(StudentGroup, id=group_id)
    group.delete()
    messages.success(request, "Group deleted successfully.")
    return redirect('view_groups')
