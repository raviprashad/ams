from django.db import models
from django.conf import settings 
from users.models import TeacherProfile

SCHOOL_CHOICES = (
    ('science_tech', 'School of Science and Technology'),
    ('forensic_science', 'School of Forensic Sciences'),
    ('legal_studies', 'School of Legal Studies'),
)


class School(models.Model):
    code = models.CharField(max_length=50, choices=SCHOOL_CHOICES, unique=True)
    
    def __str__(self):
        return dict(SCHOOL_CHOICES).get(self.code, self.code)


class Course(models.Model):
    name = models.CharField(max_length=100)
    school = models.ForeignKey('academics.School', on_delete=models.CASCADE)  

    def __str__(self):
        return self.name


class Session(models.Model):
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    course = models.ForeignKey('Course', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.course.name})"


class Semester(models.Model):
    name = models.CharField(max_length=100)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    session = models.ForeignKey('Session', on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'course', 'session'], name='unique_semester_combo'),
            models.UniqueConstraint(fields=['course', 'session', 'order'], name='unique_semester_order'),
        ]
        ordering = ['order']  # Ensures ascending semester order

    def __str__(self):
        return f"{self.name} ({self.session} - {self.course})"


# -------------------------------
# NEW MODELS
# -------------------------------

class Section(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    session = models.ForeignKey('Session', on_delete=models.CASCADE)
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = ('course', 'session', 'semester', 'name')

    def __str__(self):
        return f"{self.name} - {self.semester.name}"


class StudentGroup(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    session = models.ForeignKey('Session', on_delete=models.CASCADE)
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE)
    section = models.ForeignKey('Section', on_delete=models.SET_NULL, null=True, blank=True)  # new optional field
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = ('course', 'session', 'semester', 'name')

    def __str__(self):
        return f"{self.name} - {self.semester.name}"



class Subject(models.Model):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    teachers = models.ManyToManyField(TeacherProfile, related_name='subjects')

    def __str__(self):
        return self.name


class Holiday(models.Model):
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.date} - {self.reason}"
