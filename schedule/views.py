from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from .api import get_course_list

# Create your views here.

@login_required
def home(request):
    #Checks to make sure that the user is logged in to assign the correct name
    if request.user.is_authenticated:
        user = request.user
        role = ""
        username = user.username
    #Not Logged In is a placeholder currently
    else:
        user = "Not Logged In"
    
    #Assigns role (either Student or Advisor) based off of the user permissions
    if user.has_perm('global_permissions.is_advisor'):
        role = "Advisor"
    else:
        role = "Student"
    
    return render(request, 'schedule/home.html', {'role': role, 'username': username})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def course_search_view(request):
    courses = []
    fields = {'year': '2023', 'term': 'Fall', 'dept': '', 'instructor': ''} #default field values

    if request.method == "POST": # if search has been run
        fields = request.POST # save search fields
        courses = get_course_list( # search for courses
            year=request.POST['year'], 
            term=request.POST['term'], 
            dept=request.POST['dept'], 
            instructor=request.POST['instructor']
        )

    return render(request, 'schedule/course_search.html', {'courses': courses, 'fields': fields})