from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('course_search/', views.course_search_view, name='course_search'),
    path('add_class_to_schedule/', views.add_class_to_schedule_view, name='add_class_to_schedule'),
    path('view_submissions/', views.submissions, name='submissions'),
    path('create_schedule/', views.schedules, name='schedules'),
]
