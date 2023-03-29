from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('course_search/', views.course_search_view, name='course_search'),
    path('add_course/', views.add_course, name='add_course'),
    path('add_course_success/', views.add_course, name='add_course_success_url'),
    path('view_cart/', views.view_cart, name='view_cart'),
    path('remove-course/<int:course_id>/', views.remove_course, name='remove_course'),
    path('add-to-schedule/<int:course_id>/', views.add_to_schedule, name='add_to_schedule'),
    path('view_schedule/', views.view_schedule, name='view_schedule'),
    path('submit_schedule/', views.submit_schedule, name='submit_schedule'),
    path('submissions/', views.submissions, name='submissions')
]
