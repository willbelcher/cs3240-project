from django.urls import path, include

from . import views

app_name = 'schedule'
urlpatterns = [
    path('', views.login, name='login'),
    path('accounts/', include('allauth.urls'), name='auth'),
    path('schedule/', include('schedule.urls')),
]
