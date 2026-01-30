from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Message(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    for_teachers = models.BooleanField(default=False)
    for_students = models.BooleanField(default=False)

    def __str__(self):
        return self.title

