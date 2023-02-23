from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('home/', views.post_list, name='post_list'),
    path('accounts/', include('allauth.urls'), name='auth'),
]
