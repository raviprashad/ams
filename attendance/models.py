from django.db import models
from users.models import CustomUser
from academics.models import Subject
from timetable.models import ScheduledLecture  # ✅ use this instead of LectureSlot

class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Leave', 'Leave'),
    ]

    student = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='attendance_records'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )

    teacher = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'},
        related_name='marked_attendance_records'
    )

    lecture = models.ForeignKey(
        ScheduledLecture,  # ✅ corrected here
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('student', 'lecture')
        ordering = ['lecture__date', 'lecture__slot__lecture_number']  # Optional: sorted by date and slot

    def __str__(self):
        return (
            f"{self.student.get_full_name()} - {self.subject.name} - "
            f"{self.lecture} - {self.status}"
        )
