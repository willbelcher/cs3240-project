import django.contrib.auth.apps
from django.contrib import admin
from .models import ClassSearch, Cart, Course, Schedule, ScheduleItem

admin.site.register(ClassSearch)
admin.site.register(Cart)
admin.site.register(Course)
admin.site.register(Schedule)
admin.site.register(ScheduleItem)