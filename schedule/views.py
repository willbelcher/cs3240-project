from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout


import requests

# Create your views here.

@login_required
def home(request):
    # Checks to make sure that the user is logged in to assign the correct name
    if request.user.is_authenticated:
        user = request.user
        role = ""
        username = user.username
    # Not Logged In is a placeholder currently
    else:
        user = "Not Logged In"

    # Assigns role (either Student or Advisor) based off of the user permissions
    if user.has_perm('global_permissions.is_advisor'):
        role = "Advisor"
    else:
        role = "Student"

    return render(request, 'schedule/home.html', {'role': role, 'username': username})

# Logouts user and redirects them to the home page

def submissions(request):
    user = request.user
    if user.has_perm('global_permissions.is_advisor'):
        return render(request, 'schedule/schedule_submissions.html')


def schedules(request):
    user = request.user
    if not user.has_perm('global_permissions.is_advisor'):
        return render(request, 'schedule/schedule_creation.html')


def logout_view(request):
    logout(request)
    return redirect('home')

# Provides user with filters to search for course by year, term, department, and instructor name
subjects = [] # save subjects between searches

@login_required
def course_search_view(request):
    base_url = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch?institution=UVA01"

    field_pattern = "&{}={}"

    courses = []

    #default field values
    fields = {'year': '2023', 'term': 'Fall', 'dept': '', 'instructor': '', 'only_open': False, 'start_time': '00:00', 'end_time': '23:59'}
    days = {'Mo': True, 'Tu': True, 'We': True, 'Th': True, 'Fr': True}

    #Initialize empty sets to store unique course mnemonics, instructors
    instructors = set()

    if len(subjects) == 0: # If mnemonics not retrieved
        # TODO get different mnemonics if term is changed
        raw_subjects = requests.get("https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearchOptions?institution=UVA01&term=1228").json()

        for subject_info in raw_subjects["subjects"]:
            subjects.append(subject_info["subject"])

        subjects.sort()

    if request.method == "POST": # if search has been run
        fields = request.POST # save search fields

        year = fields.get('year')
        term = fields.get('term')
        subject = fields.get('subject')
        instructor = fields.get('instructor')
        only_open = bool(fields.get('only_open'))
        start_time = fields.get('start_time')
        end_time = fields.get('end_time')
        
        for day in days.keys():
            days[day] = bool(fields.get(day))

        if year == "":
            year = 2023

        num_term = 0
        if term == "Fall":
            num_term = 8
        elif term == "Spring":
            num_term = 2
        elif term == "Summer":
            num_term = 6

        search_url = base_url
        search_url += field_pattern.format("term", "1{}{}".format(int(year)%100, num_term))

        if subject:
            search_url += field_pattern.format("subject", subject)
        if instructor:
            search_url += field_pattern.format("instructor_name", instructor)
        if only_open:
            search_url += field_pattern.format("enrl_stat", 'O')
        
        if list(days.values()).count(True) != len(days): # Filter by days checked in form
            filter_days = ""
            for day, checked in days.items():
                if checked:
                    filter_days += day
            
            search_url += field_pattern.format("days", filter_days)

        if start_time != "00:00" or end_time != "23:59":
            start_h, start_m = start_time.split(":") # convert to sis time range format (ex. 2:30 -> 2.5)
            start_m = round(int(start_m)/30)/2

            end_h, end_m = end_time.split(":") # convert to sis time range format
            end_m = round(int(end_m)/30)/2

            formatted_range = "{}.{},{}.{}".format(start_h, start_m, end_h, end_m)
            search_url += field_pattern.format("time_range", formatted_range)

        #Store data in JSON
        # rawData = send_request(year, num_term, subject, instructor, base_url)
        # rawData = requests.get(search_url).json()
        # print(rawData)

        #Iterate through JSON
        # for course in rawData:
        #     #Add instructor name
        #     if "instructors" in course:
        #         instructors.update(
        #             [x["name"] for x in course["instructors"]]
        #             )
        # print(instructors)


        courses = requests.get(search_url).json()
    return render(request, 'schedule/course_search.html', {'courses': courses, 'fields': fields, 'subjects': subjects, 'days': days})

#method is for testing purposes
def send_request(year, num_term, subject, instructor, url):
    field_pattern = "&{}={}"
    url += field_pattern.format("term", "1{}{}".format(int(year) % 100, num_term))
    if subject:
        url += field_pattern.format("subject", subject)
    if instructor:
        url += field_pattern.format("instructor_name", instructor)

    return requests.get(url).json()
