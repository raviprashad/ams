from django import forms
from academics.models import Course, Session, Semester

class DeanAttendanceFilterForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=True)
    session = forms.ModelChoiceField(queryset=Session.objects.none(), required=True)
    semester = forms.ModelChoiceField(queryset=Semester.objects.none(), required=True)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # For POST request (when form is submitted)
        if 'course' in self.data:
            try:
                course_id = int(self.data.get('course'))
                self.fields['session'].queryset = Session.objects.filter(course_id=course_id)
            except (ValueError, TypeError):
                pass

        if 'session' in self.data:
            try:
                session_id = int(self.data.get('session'))
                self.fields['semester'].queryset = Semester.objects.filter(session_id=session_id)
            except (ValueError, TypeError):
                pass
