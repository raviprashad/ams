# to automatically create DeanProfile, StudentProfile and TeacherProfile right after a dean user is created.

from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import CustomUser, DeanProfile, TeacherProfile, StudentProfile
from academics.models import School, Course, Session, Semester

@receiver(post_save, sender=CustomUser)
def create_dean_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'dean':
        default_school = School.objects.first()
        if default_school:
            DeanProfile.objects.get_or_create(user=instance, defaults={'school': default_school})

@receiver(post_save, sender=CustomUser)
def create_student_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'student':
        # Create a blank profile — course/session/semester can be filled later
        StudentProfile.objects.get_or_create(
            user=instance,
           
        )

@receiver(post_save, sender=CustomUser)
def create_teacher_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'teacher':
        TeacherProfile.objects.get_or_create(user=instance)
