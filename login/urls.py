from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('accounts/signup/', views.signup, name="account_signup"),
    path('accounts/', include('allauth.urls'), name='auth'),
    path('schedule/', include('schedule.urls')),
]
