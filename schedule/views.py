from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from .models import Cart, Course, Schedule, ScheduleItem, User


import requests


# View for Home Page
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

# View for Submitted Schedules Page (Advisor)
def submissions(request):
    # # Get the user's cart
    #     #if the cart is created instead of get, the function returns a tuple so need to accomadate for that
    #     cart, created = Cart.objects.get_or_create(user=request.user)
    #
    #     # Get the courses associated with the cart
    #     courses = Course.objects.filter(cart=cart)
    #
    #     # Render the view_cart template with the courses
    #     context = {'courses': courses}
    #     return render(request, 'schedule/view_cart.html', context)
    user = request.user
    if user.has_perm('global_permissions.is_advisor'):
        count = 0
        schedules = Schedule.objects.filter(submitted = True).values()
        context = {'schedules':[]}

        for schedule in schedules:
            users = User.objects.get(pk=schedule['user_id'])
            items = ScheduleItem.objects.filter(schedule=schedule['id']).values()

            context['schedules'].append({'user': users, 'courses':[]})
            for item in items:
                    course = Course.objects.get(pk=item['course_id'])
                    context['schedules'][count]['courses'].append(course)
            count = count + 1

        return render(request, 'schedule/schedule_submissions.html', context)

# Logouts user and redirects them to the home page
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
    fields = {'year': '2023', 'term': 'Fall', 'dept': '', 'instructor': '', 'course_name': '', 'course_nmbr': '', 'only_open': False, 'start_time': '00:00', 'end_time': '23:59'}
    days = {'Mo': True, 'Tu': True, 'We': True, 'Th': True, 'Fr': True}

    #Initialize empty sets to store instructors
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
        course_name = fields.get('course_name')
        course_nmbr = fields.get('course_nmbr')
        catalog_nbr = fields.get('catalog_nbr')
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
        if course_name:
            search_url += field_pattern.format("keyword", course_name)
        if course_nmbr:
            search_url += field_pattern.format("class_nbr", course_nmbr)
        if catalog_nbr:
            search_url += field_pattern.format("catalog_nbr", catalog_nbr)
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

        print(search_url)
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

def get_subjects():
    raw_subjects = requests.get(
        "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearchOptions?institution=UVA01&term=1228").json()

    for subject_info in raw_subjects["subjects"]:
        subjects.append(subject_info["subject"])

    subjects.sort()

    return subjects

# View to Add Course to Cart
@login_required
def add_course(request):
    subjects = get_subjects()
    if request.method == 'POST':
        term = request.POST.get('term', '').strip()
        class_nbr = request.POST.get('class_nbr', '').strip()

        # Validate input
        if not term:
            messages.error(request, 'Term is required. we got', term)
        elif not class_nbr:
            messages.error(request, 'Class Number is required.')
        else:
            # Build the SIS API URL
            url = f'https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch?institution=UVA01&term={term}&class_nbr={class_nbr}'

            # Make the request to the SIS API
            response = requests.get(url)

            if response.status_code == 200:

                # Parse the JSON response
                json_data = response.json()
                course_data = json_data[0]  # Assuming the course data is in the first element of the list

                # Extract course information
                subject = course_data['subject']
                catalog_nbr = course_data['catalog_nbr']
                title = course_data['descr']
                instructor_name = course_data['instructors'][0]['name']

                # Save the course to the user's cart
                cart, _ = Cart.objects.get_or_create(user=request.user)
                course = Course(cart=cart, class_nbr=class_nbr, subject=subject, catalog_nbr=catalog_nbr, title=title, instructor_name=instructor_name)
                course.save()

                messages.success(request, 'Course added successfully!')
                return redirect('add_course_success_url')
            else:
                messages.error(request, 'Failed to fetch course data.')

   #resest all the filters so the website doesn't break on a following course search
    days = {'Mo': True, 'Tu': True, 'We': True, 'Th': True, 'Fr': True}
    fields = {'start_time' : "00:00", 'end_time':"23:59"}
    return render(request, 'schedule/course_search.html', {'subjects': subjects, 'fields':fields, 'days':days})

# View for View Cart Page
@login_required
def view_cart(request):
    # Get the user's cart
    #if the cart is created instead of get, the function returns a tuple so need to accommodate for that
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Get the courses associated with the cart
    courses = Course.objects.filter(cart=cart)

    # Render the view_cart template with the courses
    context = {'courses': courses}
    return render(request, 'schedule/view_cart.html', context)
# Removes a course from the user's cart
@login_required
def remove_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, cart__user=request.user)
    course.delete()
    messages.success(request, 'Course removed from cart.')
    return redirect('view_cart')

# Adds a course to the user's schedule from their cart
@login_required
def add_to_schedule(request, course_id):
    course = get_object_or_404(Course, id=course_id, cart__user=request.user)
    schedule, _ = Schedule.objects.get_or_create(user=request.user)
    schedule_item = ScheduleItem(schedule=schedule, course=course)
    schedule_item.save()
    messages.success(request, 'Course added to schedule.')
    return redirect('view_cart')

# View for View Schedule Page
@login_required
def view_schedule(request):
    schedule = get_object_or_404(Schedule, user=request.user)
    schedule_items = ScheduleItem.objects.filter(schedule=schedule)
    context = {
        'schedule': schedule,
        'schedule_items': schedule_items,
    }
    return render(request, 'schedule/view_schedule.html', context)

# Submits schedule to advisor
@login_required
def submit_schedule(request):
    schedule = get_object_or_404(Schedule, user=request.user)

    # Replace "advisor_username" with the username of the student's advisor username
    advisor = get_object_or_404(User, username="devang6")
    schedule.advisor = advisor
    schedule.submitted = True
    schedule.save()
    messages.success(request, 'Schedule submitted to advisor.')
    return redirect('view_schedule')