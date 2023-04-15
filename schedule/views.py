from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from .models import Cart, Course, Schedule, ScheduleItem, User, CourseTime
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
        schedule['color'] = color_dict[schedule['status'].lower()]

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

@login_required
def course_search_view(request):
    base_url = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch?institution=UVA01"

    field_pattern = "&{}={}"

    courses = []

    #default field values
    fields = {'year': '2023', 'term': 'Fall', 'dept': '', 'instructor': '', 'course_name': '', 'course_nmbr': '', 'only_open': False, 'start_time': '00:00', 'end_time': '23:59'}
    days = {'Mo': True, 'Tu': True, 'We': True, 'Th': True, 'Fr': True}
    active_class_messages = False
    no_classes_found = False
    class_messages = []

    #Initialize empty sets to store instructors
    instructors = set()

    if len(subjects) == 0: # If mnemonics not retrieved
        raw_subjects = requests.get(
            "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearchOptions?institution=UVA01&term=1228").json()

        for subject_info in raw_subjects["subjects"]:
            subjects.append(subject_info["subject"])

        subjects.sort()

    if request.method == "POST": # if search has been run
        fields = request.POST.copy() # save search fields

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

        if subject == "" and (start_time == "00:00" and end_time == "23:59"):
            messages.error(request, "Please enter a more specific search")
            active_class_messages = True
            class_messages.append("A Subject or Specific Time range is required")
            return render(request, 'schedule/course_search.html', {'subjects': subjects, 'fields': fields, 'days': days,
                                                                   'active_class_messages':active_class_messages,
                                                                   'class_messages': class_messages})

        if not catalog_nbr.isnumeric() and not catalog_nbr == "" :
            fields['catalog_nbr'] = ""
            catalog_nbr=""
            active_class_messages = True
            class_messages.append("Catalog Number Field returned to default value")
        if not course_nmbr.isnumeric() and not course_nmbr == "":
            course_nmbr = ""
            fields['course_nmbr'] = ""
            active_class_messages = True
            class_messages.append("Course Number Field returned to default value")
        if " " in instructor:
            instructor = instructor.split(" ")[0]
            active_class_messages = True
            class_messages.append("Instructor Field has been reverted to a valid value")
        if " " in course_name:
            course_name = course_name.split(" ")[0]
            active_class_messages = True
            class_messages.append("Course Name Field has been reverted to a valid value")
        
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
            start_time = float(start_h) + float(start_m)

            end_h, end_m = end_time.split(":") # convert to sis time range format
            end_m = round(int(end_m)/30)/2
            end_time = float(end_h) + float(end_m)

            if start_time == 0.0:
                start_time = 0.5
            if end_time == 24.0:
                end_time = 23.5
            formatted_range = "{},{}".format(start_time, end_time)
            search_url += field_pattern.format("time_range", formatted_range)

        print(search_url)
        courses = requests.get(search_url).json()
        if len(courses) == 0:
            no_classes_found = True
    return render(request, 'schedule/course_search.html', {'courses': courses, 'fields': fields, 'subjects': subjects,
                                                           'days': days, 'active_class_messages' : active_class_messages,
                                                           'class_messages': class_messages,
                                                           'no_classes_found':no_classes_found})

#method is for testing purposes
def send_request(year, num_term, subject, instructor, url):
    field_pattern = "&{}={}"
    url += field_pattern.format("term", "1{}{}".format(int(year) % 100, num_term))
    if subject:
        url += field_pattern.format("subject", subject)
    if instructor:
        url += field_pattern.format("instructor_name", instructor)

    return requests.get(url).json()

def add_course_success(request):
    pass

# View to Add Course to Cart
@login_required
def add_course(request):
    days = {'Mo': True, 'Tu': True, 'We': True, 'Th': True, 'Fr': True}
    fields = {'start_time': "00:00", 'end_time': "23:59"}
    active_class_messages = False
    class_messages = []
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
                units = int(course_data['units'])

                # Save the course to the user's cart
                cart, _ = Cart.objects.get_or_create(user=request.user)

                courses_in_cart = Course.objects.filter(cart=cart)
                if courses_in_cart:
                    for cart_course in courses_in_cart:
                        if cart_course.subject == subject and cart_course.catalog_nbr == catalog_nbr:
                            messages.error(request, "Can not add identical course to Cart")
                            active_class_messages = True
                            class_messages.append("Can not add an identical course to Cart")
                            return render(request, 'schedule/course_search.html', {'subjects': subjects, 'fields': fields, 'days': days, 'active_class_messages':active_class_messages, 'class_messages':class_messages})

                course = Course(cart=cart, class_nbr=class_nbr, subject=subject, catalog_nbr=catalog_nbr, title=title, instructor_name=instructor_name, units=units)
                course.save()

                for json_days in course_data['meetings']:
                    start_time = json_days['start_time'][0:5].replace(".", ":")
                    end_time = json_days['end_time'][0:5].replace(".", ":")
                    all_days = json_days['days']

                    time = CourseTime.objects.create(course=course, days=all_days, starting_time=start_time, ending_time=end_time)
                    time.save()

                active_class_messages = True
                class_messages.append("Course added successfully!")
                messages.success(request, 'Course added successfully!')

                return redirect('schedule:add_course_success')
            else:
                messages.error(request, 'Failed to fetch course data.')

   #resest all the filters so the website doesn't break on a following course search
    return render(request, 'schedule/course_search.html', {'subjects': subjects, 'fields':fields, 'days':days, 'active_class_messages':active_class_messages, 'class_messages':class_messages})


# View for View Cart Page
@login_required
def view_cart(request):
    # Get the user's cart
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Get the user's schedule
    schedule, _ = Schedule.objects.get_or_create(user=request.user)

    # Get the courses associated with the cart and exclude those in the user's schedule
    courses = Course.objects.filter(cart=cart).exclude(scheduleitem__schedule=schedule)

    # Render the view_cart template with the courses
    context = {'courses': courses, 'schedule_submitted':schedule.submitted}
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
    total_units = schedule.total_units

    times = CourseTime.objects.filter(course = course) #get all meetings of course thats to be added
    items = ScheduleItem.objects.filter(schedule=schedule.id)
    for item in items:
        added_course = Course.objects.get(pk = item.course.id) #get all courses already in schedule

        if added_course.subject == course.subject and added_course.catalog_nbr == course.catalog_nbr:
            cart, _ = Cart.objects.get_or_create(user=request.user)

            # Get the courses associated with the cart and exclude those in the user's schedule
            courses = Course.objects.filter(cart=cart).exclude(scheduleitem__schedule=schedule)

            # Render the view_cart template with the courses
            context = {'courses': courses, 'active_class_messages': True,
                       'class_messages': "Can not add this course, the same course is already added"}
            return render(request, 'schedule/view_cart.html', context)

        added_course_times = CourseTime.objects.filter(course = added_course) #get these already-added course times
        for time in times:
            time_starting_hour = int(time.starting_time.split(":")[0])
            time_ending_hour = int(time.ending_time.split(":")[0])

            # splits each day string "MoWe" into tokens of 2 characters ["Mo", "We"]
            split_days = [time.days[i:i + 2] for i in range(0, len(time.days), 2)]

            for added_course_time in added_course_times:
                for day in split_days:
                    # if the to-be-added course has any day in common with an existing class
                    if day in added_course_time.days:
                        added_course_starting_hour = int(added_course_time.starting_time.split(":")[0])
                        added_course_ending_time = int(added_course_time.ending_time.split(":")[0])

                        if added_course_starting_hour <= time_starting_hour <= added_course_ending_time or \
                                time_starting_hour <= added_course_starting_hour <= time_ending_hour:
                            messages.error(request, 'Courses overlap!')
                            course.save()
                            # Get the user's cart
                            cart, _ = Cart.objects.get_or_create(user=request.user)

                            # Get the courses associated with the cart and exclude those in the user's schedule
                            courses = Course.objects.filter(cart=cart).exclude(scheduleitem__schedule=schedule)

                            # Render the view_cart template with the courses
                            context = {'courses': courses, 'active_class_messages':True, 'class_messages':"Can not add this course, it overlaps with a class already in your schedule."}
                            return render(request, 'schedule/view_cart.html', context)

    if schedule.total_units + course.units > 19:
        # Get the user's cart
        print(total_units)
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # Get the courses associated with the cart and exclude those in the user's schedule
        courses = Course.objects.filter(cart=cart).exclude(scheduleitem__schedule=schedule)

        # Render the view_cart template with the courses
        context = {'courses': courses, 'active_class_messages': True,
                   'class_messages': "Can not add this course, it will surpass the 19 credit limit."}
        return render(request, 'schedule/view_cart.html', context)
    schedule.total_units = total_units + course.units
    if schedule.submitted:
        schedule.submitted = False
    schedule.save()

    schedule_item = ScheduleItem(schedule=schedule, course=course)
    schedule_item.save()

    course.cart = None
    course.save()

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

def remove_course_from_schedule(request, course_id):
    # course = get_object_or_404(Course, id=course_id, cart__user=request.user)
    # course.delete()
    # messages.success(request, 'Course removed from cart.')
    # return redirect('schedule:view_cart')
    schedule = get_object_or_404(Schedule, user=request.user)
    course = get_object_or_404(Course, pk = course_id)
    schedule.total_units = schedule.total_units - course.units
    course.delete()
    schedule.save()
    # schedule_item = ScheduleItem.objects.get(course = course)
    # schedule_item.delete()
    messages.success(request, 'Removed Course from the Schedule')
    return redirect('schedule:view_schedule')

def unsubmit_schedule(request):
    schedule = get_object_or_404(Schedule, user = request.user)
    schedule.submitted = False
    schedule.save()
    return redirect('schedule:view_schedule')

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