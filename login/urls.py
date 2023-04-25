from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('accounts/', include('allauth.urls'), name='auth'),
    path('schedule/', include('schedule.urls')),
    #sign in without google
    path('sign up', views.signup ,name='signup'),
   
]
