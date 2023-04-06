from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class ClassSearch(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title
    
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class Course(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    class_nbr = models.IntegerField()
    subject = models.CharField(max_length=10)
    catalog_nbr = models.CharField(max_length=10)
    instructor_name = models.CharField(max_length=50)
    title = models.CharField(max_length=200)


class Schedule(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    advisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='schedules_advised')
    submitted = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Denied', 'Denied'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True, null=True)

class ScheduleItem(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)