from django import forms
from .models import LectureSlot
from academics.models import Subject
from users.models import TeacherProfile

from django import forms
from .models import LectureSlot
from users.models import TeacherProfile

from django import forms
from .models import LectureSlot
from users.models import TeacherProfile

class LectureSlotForm(forms.ModelForm):
    class Meta:
        model = LectureSlot
        fields = ['subject', 'teacher', 'day_of_week', 'lecture_number', 'section', 'group']  # added section, group

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['teacher'].queryset = TeacherProfile.objects.filter(user__is_active=True)
        self.fields['subject'].label = "Subject"
        self.fields['teacher'].label = "Assigned Teacher"
        self.fields['day_of_week'].label = "Day of Week"
        self.fields['lecture_number'].label = "Lecture Number"
        self.fields['section'].label = "Section (optional)"
        self.fields['group'].label = "Group (optional)"

        # If you want, you can limit queryset for section/group here
        # self.fields['section'].queryset = Section.objects.all()
        # self.fields['group'].queryset = StudentGroup.objects.all()

        # Both fields are optional, so no required=True

    def clean(self):
        cleaned_data = super().clean()
        teacher = cleaned_data.get('teacher')
        day_of_week = cleaned_data.get('day_of_week')
        lecture_number = cleaned_data.get('lecture_number')

        if teacher and day_of_week and lecture_number:
            conflict = LectureSlot.objects.filter(
                teacher=teacher,
                day_of_week=day_of_week,
                lecture_number=lecture_number
            ).exclude(id=self.instance.id).exists()

            if conflict:
                raise forms.ValidationError(
                    f"{teacher.user.get_full_name()} already has a lecture scheduled "
                    f"on {day_of_week} during slot {lecture_number}."
                )
        return cleaned_data


# timetable/forms.py
from django import forms
from users.models import TeacherProfile

from django import forms
from users.models import TeacherProfile
from academics.models import Subject

# timetable/forms.py
from django import forms
from users.models import TeacherProfile
from academics.models import Subject

class AssignSubstituteForm(forms.Form):
    substitute_teacher = forms.ModelChoiceField(
        queryset=TeacherProfile.objects.none(),
        label="Choose a teacher",
        widget=forms.Select(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2'})
    )
    substitute_subject = forms.ModelChoiceField(
        queryset=Subject.objects.none(),
        label="Choose a subject",
        widget=forms.Select(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2'})
    )

    def __init__(self, *args, eligible_teachers=None, teacher_subject_map=None, **kwargs):
        super().__init__(*args, **kwargs)
        if eligible_teachers:
            self.fields['substitute_teacher'].queryset = eligible_teachers
        if teacher_subject_map:
            self.teacher_subject_map = teacher_subject_map

        # Handle dynamic subject choices based on selected teacher
        if 'substitute_teacher' in self.data:
            try:
                teacher_id = int(self.data.get('substitute_teacher'))
                self.fields['substitute_subject'].queryset = teacher_subject_map.get(teacher_id, Subject.objects.none())
            except (ValueError, TypeError):
                pass
