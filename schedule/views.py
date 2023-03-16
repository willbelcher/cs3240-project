from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

import requests
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
    base_url = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch?institution=UVA01"
    field_pattern = "&{}={}"
    
    courses = []
    fields = {'year': '2023', 'term': 'Fall', 'dept': '', 'instructor': ''} #default field values
    
    if request.method == "POST": # if search has been run
        fields = request.POST # save search fields

        year = fields.get('year', 2023)
        term = fields.get('term', 'Fall')
        dept = fields.get('dept', False)
        instructor = fields.get('instructor', False)

        if year == "":
            year = 2023
        
        num_term = 0
        if term == "Fall":
            num_term = 8
        elif term == "Spring":
            num_term = 2

        search_url = base_url
        search_url += field_pattern.format("term", "1{}{}".format(int(year)%100, num_term))

        if dept:
            search_url += field_pattern.format("subject", dept)
        if instructor:
            search_url += field_pattern.format("instructor_name", instructor)
        
        resp = requests.get(search_url)
        courses = resp.json()

    return render(request, 'schedule/course_search.html', {'courses': courses, 'fields': fields})


