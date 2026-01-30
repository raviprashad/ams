from django.db import models
from django.conf import settings

class LeaveRequest(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    certificate = models.FileField(upload_to='certificates/', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_forwarded_by_dean = models.BooleanField(default=False)


    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Leave by {self.student.username} ({self.start_date} to {self.end_date})"


class LeaveApproval(models.Model):
    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name="approvals")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[('approved', 'Approved'), ('rejected', 'Rejected')])
    responded_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.teacher.username} - {self.status}"
