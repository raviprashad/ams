from django.db import models
from academics.models import Subject, Section, StudentGroup
from users.models import TeacherProfile

class LectureSlot(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    lecture_number = models.PositiveIntegerField()

    # Optional differentiators
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.SET_NULL)
    group = models.ForeignKey(StudentGroup, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        sec = f" - Section: {self.section.name}" if self.section else ""
        grp = f" - Group: {self.group.name}" if self.group else ""
        return f"{self.subject.name}{sec}{grp} - {self.day_of_week} - Lecture {self.lecture_number}"


class ScheduledLecture(models.Model):
    slot = models.ForeignKey(LectureSlot, on_delete=models.CASCADE)
    date = models.DateField()  # Actual calendar date of the lecture

    # These fields are auto-filled from the slot
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, editable=False)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, editable=False)
    lecture_number = models.PositiveIntegerField(editable=False)

    # Optional differentiators, copied from slot to keep reference intact
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.SET_NULL, editable=False)
    group = models.ForeignKey(StudentGroup, null=True, blank=True, on_delete=models.SET_NULL, editable=False)

    # Substitution-related fields
    substitute_teacher = models.ForeignKey(
        TeacherProfile,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='substituted_lectures'
    )
    substitute_subject = models.ForeignKey(
        Subject,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='substituted_subjects'
    )

    class Meta:
        unique_together = ('slot', 'date')
        ordering = ['date', 'lecture_number']

    def save(self, *args, **kwargs):
        """
        Auto-fill teacher, subject, lecture_number, section, and group from slot unless substitution is set.
        """
        if self.substitute_teacher:
            self.teacher = self.substitute_teacher
            self.subject = self.substitute_subject or self.slot.subject
        else:
            self.teacher = self.slot.teacher
            self.subject = self.slot.subject

        self.lecture_number = self.slot.lecture_number
        self.section = self.slot.section
        self.group = self.slot.group

        super().save(*args, **kwargs)

    def get_responsible_teacher(self):
        """
        Returns the teacher responsible for this lecture (substitute or original).
        """
        return self.teacher

    def is_original_teacher(self, user):
        """
        Check if given user is original teacher for this lecture.
        """
        return self.slot.teacher.user == user

    def is_substitute_teacher(self, user):
        """
        Check if given user is substitute teacher for this lecture.
        """
        return self.substitute_teacher is not None and self.substitute_teacher.user == user

    def __str__(self):
        sec = f"Section: {self.section.name}, " if self.section else ""
        grp = f"Group: {self.group.name}, " if self.group else ""
        return f"{self.subject.name} - {sec}{grp}Teacher: {self.teacher.user.get_full_name()} on {self.date} (Lecture {self.lecture_number})"
