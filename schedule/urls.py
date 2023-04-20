from django.urls import path, include

from . import views

app_name = 'schedule'
urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('course_search/', views.course_search_view, name='course_search'),
    path('add_course/', views.add_course, name='add_course'),
    path('add_course_success/', views.add_course, name='add_course_success'),
    path('view_cart/', views.view_cart, name='view_cart'),
    path('remove-course/<int:course_id>/', views.remove_course, name='remove_course'),
    path('add-to-schedule/<int:schedule_id>/<int:course_id>/', views.add_to_schedule, name='add_to_schedule'),
    path('view_schedule/', views.view_schedule, name='view_schedule'),
    path('remove_schedule_course/<int:schedule_id>/<int:course_id>', views.remove_course_from_schedule, name='remove_course_from_schedule'),
    path('submit_schedule/<int:schedule_id>/', views.submit_schedule, name='submit_schedule'),
    path('unsubmit_schedule/<int:schedule_id>/', views.unsubmit_schedule, name='unsubmit_schedule'),
    path('submissions/', views.submissions, name='submissions'),
    path('approve-schedule/<int:schedule_id>/', views.approve_schedule, name='approve_schedule'),
    path('deny-schedule/<int:schedule_id>/', views.deny_schedule, name='deny_schedule'),
    path('add_comments/<int:schedule_id>/', views.add_comments, name='add_comments'),
    path('delete_schedule/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),
    path('create_schedule/', views.create_schedule, name='create_schedule'),
    path('rename_schedule/<int:schedule_id>/', views.rename_schedule, name='rename_schedule'),
]
