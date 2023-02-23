from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('accounts/', include('allauth.urls'), name='auth'),
]
