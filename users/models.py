from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.conf import settings

ROLE_CHOICES = (
    ('dean', 'Dean'),
    ('teacher', 'Teacher'),
    ('student', 'Student'),
)


class CustomUser(AbstractUser):
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    school = models.ForeignKey('academics.School', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.get_full_name() or self.username


class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    course = models.ForeignKey('academics.Course', on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey('academics.Session', on_delete=models.CASCADE, null=True, blank=True)
    semester = models.ForeignKey('academics.Semester', on_delete=models.CASCADE, null=True, blank=True)
    
    # NEW — optional section & group fields
    section = models.ForeignKey('academics.Section', on_delete=models.SET_NULL, null=True, blank=True)
    group = models.ForeignKey('academics.StudentGroup', on_delete=models.SET_NULL, null=True, blank=True)

    enrollment_number = models.CharField(max_length=50, null=True, blank=True) 
    is_active = models.BooleanField(default=True)  

    def clean(self):
        if self.user_id and self.user.role != 'student':
            raise ValidationError('Only users with role "student" can have a StudentProfile.')

    def __str__(self):
        course_name = self.course.name if self.course else "No Course"
        return f"{self.user.username} - {course_name}"


class TeacherProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.user.username  


class DeanProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'dean'})
    school = models.ForeignKey('academics.School', on_delete=models.CASCADE)  

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.school.name}"
