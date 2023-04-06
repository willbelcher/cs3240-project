from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from .models import Cart, Course, Schedule, ScheduleItem, User
import requests
from django.http import HttpResponse


# View for Home Page
@login_required
def home(request):
    color_dict = {"pending": "yellow", "approved": "green", "denied": "red"}

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

    schedules = Schedule.objects.filter(user=request.user).values()
    has_schedule = len(schedules) != 0

    schedule = {"exists": has_schedule, "color": None, "status": None}
    if has_schedule:
        schedule['status'] = schedules[0]['status']
        schedule['color'] = color_dict[schedule['status']]

    return render(request, 'schedule/home.html', {'role': role, 'username': username, 'schedule': schedule})

# View for Submitted Schedules Page (Advisor)
def submissions(request):
    user = request.user
    if user.has_perm('global_permissions.is_advisor'):
        count = 0
        schedules = Schedule.objects.filter(submitted = True).values()
        context = {'schedules': []}

        for schedule in schedules:
            users = User.objects.get(pk=schedule['user_id'])
            items = ScheduleItem.objects.filter(schedule=schedule['id']).values()

            context['schedules'].append({'user': users, 'courses':[]})
            for item in items:
                    course = Course.objects.get(pk=item['course_id'])
                    context['schedules'][count]['courses'].append(course)
            count = count + 1
        schedules = Schedule.objects.filter(submitted=True)
        context.update({'schedules': schedules})

        return render(request, 'schedule/schedule_submissions.html', context)
    else:

        return HttpResponse("You are not authorized to view this page.")
    

# Logouts user and redirects them to the home page
def logout_view(request):
    logout(request)
    return redirect('schedule:home')

# Provides user with filters to search for course by year, term, department, and instructor name
subjects = [] # save subjects between searches
day_map = {'Mo': 'M', 'Tu': 'T', 'We': 'W', 'Th': 'R', 'Fr': 'F'}

@login_required
def course_search_view(request):
    base_url = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch?institution=UVA01"

    field_pattern = "&{}={}"

    courses = []

    #default field values
    days = {'Mo': True, 'Tu': True, 'We': True, 'Th': True, 'Fr': True}
    fields = {'year': '2023', 'term': 'Fall', 'dept': '', 'instructor': '', 'course_name': '', 'course_nmbr': '', 'only_open': False, 'start_time': '00:00', 'end_time': '23:59'}
    
    #reloads params if search has been run
    if request.session.has_key('search_params'):
        fields = request.session.get('search_params')

        for day in days.keys():
            days[day] = fields.get(day)

    if len(subjects) == 0: # If mnemonics not retrieved
        get_subjects()

    if request.method == "POST": # if search has been run
        fields = request.POST.dict() # save search fields

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

        fields['only_open'] = only_open
        
        for day in days.keys():
            days[day] = bool(fields.get(day))
            fields[day] = days[day]

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
            filter_days = []
            for day, checked in days.items():
                if checked:
                    filter_days.append(day_map[day])
            
            search_url += field_pattern.format("days", ",".join(filter_days))

        if start_time != "00:00" or end_time != "23:59":
            start_h, start_m = start_time.split(":") # convert to sis time range format (ex. 2:30 -> 2.5)
            start_m = round(int(start_m)/30)/2

            end_h, end_m = end_time.split(":") # convert to sis time range format
            end_m = round(int(end_m)/30)/2

            formatted_range = "{}.{},{}.{}".format(start_h, start_m, end_h, end_m)
            search_url += field_pattern.format("time_range", formatted_range)

        request.session['search_params'] = fields
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

def add_course_success(request):
    pass

# View to Add Course to Cart
@login_required
def add_course(request):
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
                return redirect('schedule:add_course_success')
            else:
                messages.error(request, 'Failed to fetch course data.')

    return redirect('schedule:course_search')


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
    return redirect('schedule:view_cart')

# Adds a course to the user's schedule from their cart
@login_required
def add_to_schedule(request, course_id):
    course = get_object_or_404(Course, id=course_id, cart__user=request.user)
    schedule, _ = Schedule.objects.get_or_create(user=request.user)
    schedule_item = ScheduleItem(schedule=schedule, course=course)
    schedule_item.save()
    messages.success(request, 'Course added to schedule.')
    return redirect('schedule:view_cart')

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
    advisor = get_object_or_404(User, username="glendonchin")
    schedule.advisor = advisor
    schedule.submitted = True
    schedule.save()
    messages.success(request, 'Schedule submitted to advisor.')
    return redirect('schedule:view_schedule')


from django.contrib.auth.decorators import user_passes_test

# Helper function to check if a user is an advisor
def is_advisor(user):
    is_advisor = user.groups.filter(name='glendonchin').exists()
    print(f"User {user.username} is advisor: {is_advisor}")
    return user.groups.filter(name='glendonchin').exists()

@login_required
@user_passes_test(is_advisor)
def approve_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    schedule.status = 'approved'
    schedule.save()
    # Redirect to the submissions page
    return redirect('schedule:submissions')

@login_required
@user_passes_test(is_advisor)
def deny_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    if request.method == 'POST':
        comments = request.POST.get('comments')
        schedule.status = 'denied'
        schedule.comments = comments
        schedule.save()
        # Redirect to the submissions page
        return redirect('schedule:submissions')
    else:
        # Render the deny schedule form
        return render(request, 'deny_schedule.html', {'schedule': schedule})