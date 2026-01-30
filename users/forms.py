from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, StudentProfile, TeacherProfile
from academics.models import School, Course, Session, Semester
from django.core.exceptions import ValidationError


class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'school']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)



class AddTeacherForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']  

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        email = self.cleaned_data['email']
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        password = CustomUser.objects.make_random_password()
        school = self.request.user.school  

        user = CustomUser.objects.create_user(
            username=first_name,  
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            role='teacher',
            school=school
        )

        if commit:
            user.save()
        self.generated_password = password
        return user



#when dean adds students
class AddStudentForm(forms.ModelForm):
    email = forms.EmailField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    enrollment_number = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': ''}),
        max_length=50
    )
    class Meta:
        model = StudentProfile
        fields = ['course', 'session', 'semester','enrollment_number']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(username=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        email = self.cleaned_data['email']
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        password = CustomUser.objects.make_random_password()
        self.generated_password = password  # store password in form

        user = CustomUser.objects.create_user(
            username=first_name,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            role='student'
        )

        student_profile = super().save(commit=False)
        student_profile.user = user

        if commit:
            user.save()
            student_profile.save()

        return student_profile




class EditStudentForm(forms.ModelForm):
    username = forms.CharField()
    email = forms.EmailField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    enrollment_number = forms.CharField(max_length=50)
    course = forms.ModelChoiceField(queryset=Course.objects.all())
    session = forms.ModelChoiceField(queryset=Session.objects.all())
    semester = forms.ModelChoiceField(queryset=Semester.objects.all())

    class Meta:
        model = StudentProfile
        fields = ['course', 'session', 'semester', 'enrollment_number']

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)
        if self.user_instance:
            self.fields['username'].initial = self.user_instance.username
            self.fields['email'].initial = self.user_instance.email
            self.fields['first_name'].initial = self.user_instance.first_name
            self.fields['last_name'].initial = self.user_instance.last_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(pk=self.user_instance.pk).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exclude(pk=self.user_instance.pk).exists():
            raise ValidationError("A user with this username already exists.")
        return username

    def save(self, commit=True):
        student_profile = super().save(commit=False)
        user = self.user_instance

        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            student_profile.user = user
            student_profile.save()

        return student_profile


class EditTeacherForm(forms.ModelForm):
    username = forms.CharField()
    email = forms.EmailField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    
    class Meta:
        model = TeacherProfile
        fields = []
    

    

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)

        if self.user_instance:
            self.fields['username'].initial = self.user_instance.username
            self.fields['email'].initial = self.user_instance.email
            self.fields['first_name'].initial = self.user_instance.first_name
            self.fields['last_name'].initial = self.user_instance.last_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(pk=self.user_instance.pk).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exclude(pk=self.user_instance.pk).exists():
            raise ValidationError("A user with this username already exists.")
        return username

    def save(self, commit=True):
        teacher = super().save(commit=False)
        user = self.user_instance
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            teacher.user = user
            teacher.save()
            self.save_m2m()
        return teacher