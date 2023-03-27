from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('course_search/', views.course_search_view, name='course_search'),
    path('view_submissions/', views.submissions, name='submissions'),
    path('create_schedule/', views.schedules, name='schedules'),
    path('add_course/', views.add_course, name='add_course'),
    path('view_cart/', views.view_cart, name='view_cart'),
]
