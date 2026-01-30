from django.contrib import admin
from .models import Course, Subject, Session, Semester, School
admin.site.register(School)
admin.site.register(Course)
admin.site.register(Subject)
admin.site.register(Session)
admin.site.register(Semester)



