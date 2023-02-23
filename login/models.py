from django.db import models
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# Create your models here.
class Users(models.Model):
    user_name = models.CharField(max_length=200)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date pulbished')
    class Meta:
        permissions = [
            ("admin", "Can approve schedules"),
            ("close_task", "Can make schedules")
        ]