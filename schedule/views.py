from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import Cart, Course


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
    fields = {'year': '2023', 'term': 'Fall', 'dept': '', 'instructor': '', 'only_open': False} #default field values

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
    return render(request, 'schedule/course_search.html', {'courses': courses, 'fields': fields, 'subjects': subjects})

#method is for testing purposes
def send_request(year, num_term, subject, instructor, url):
    field_pattern = "&{}={}"
    url += field_pattern.format("term", "1{}{}".format(int(year) % 100, num_term))
    if subject:
        url += field_pattern.format("subject", subject)
    if instructor:
        url += field_pattern.format("instructor_name", instructor)

    return requests.get(url).json()


@login_required
def add_course(request):
    if request.method == 'POST':
        # Get the required data from the form
        term = request.POST['term']
        class_nbr = request.POST['class_nbr']

        # Build the URL
        base_url = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch?institution=UVA01"
        url = f"{base_url}&term={term}&class_nbr={class_nbr}"

        # Make the request
        response = requests.get(url)
        course_data = response.json()

        # Create a new course and add it to the cart
        course = Course(
            class_nbr=class_nbr,
            subject=course_data['subject'],
            catalog_nbr=course_data['catalog_nbr'],
            instructor_name=course_data['instructor_name'],
            title=course_data['title']
        )

        # Get the user's cart or create one if it doesn't exist
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # Add the course to the cart
        course.cart = cart
        course.save()

        return render(request, 'add_course_success.html')

    return render(request, 'add_course_form.html')

@login_required
def view_cart(request):
    # Get the user's cart
    cart = Cart.objects.get(user=request.user)

    # Get the courses associated with the cart
    courses = Course.objects.filter(cart=cart)

    # Render the view_cart template with the courses
    context = {'courses': courses}
    return render(request, 'view_cart.html', context)