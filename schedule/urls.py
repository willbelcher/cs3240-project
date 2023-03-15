from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('course_search/', views.course_search_view, name='course_search'),
]
