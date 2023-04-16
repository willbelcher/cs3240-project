import requests
from django.http.response import Http404
from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from schedule.views import send_request, add_course, remove_course, add_to_schedule, view_schedule, submissions, \
    view_cart, remove_course_from_schedule, unsubmit_schedule, submit_schedule, is_advisor, approve_schedule, \
    deny_schedule
from schedule.models import Course, Schedule, ScheduleItem, User

# Create your tests here.
def addDummyCourse(factory, user):
    request = factory.post('schedule/add_course', {'term': '1238', 'class_nbr': '15337'})

    setupRequest(request, user)

    add_course(request)
    return Course.objects.all().values()[0]['id']


def setupRequest(request, user):
    request.user = user

    middleware = SessionMiddleware(request)
    middleware.process_request(request)
    request.session.save()

    request._messages = FallbackStorage(request)


class TestCourseSearch(TestCase):
    def test_invalid_instructor(self):
        field_pattern = "&{}={}"
        year = 2023
        num_term = 8 #Fall semester
        subject = 'APMA'
        instructor = 'asdkjflasdjf9834random'
        base = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch?institution=UVA01"
        search_url = base + field_pattern.format("term", "1{}{}".format(int(year)%100, num_term))
        search_url += field_pattern.format("subject", subject)
        search_url += field_pattern.format("instructor_name", instructor)

        test_response = send_request(year, num_term, subject, instructor, base)

        self.assertEqual(test_response, [])

    def test_valid_instructor(self):
        field_pattern = "&{}={}"
        year = 2023
        num_term = 8 #Fall semester
        subject = 'APMA'
        instructor = 'Hellings'
        base = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch?institution=UVA01"
        search_url = base + field_pattern.format("term", "1{}{}".format(int(year)%100, num_term))
        search_url += field_pattern.format("subject", subject)
        search_url += field_pattern.format("instructor_name", instructor)
        control_response = requests.get(search_url).json()

        test_response = send_request(year, num_term, subject, instructor, base)

        self.assertEqual(test_response, control_response)

    def test_instructor_not_in_subject(self):
        field_pattern = "&{}={}"
        year = 2023
        num_term = 8  # Fall semester
        subject = 'TURK' #Hellings does not teach any classes in the Turkish Department
        instructor = 'Hellings'
        base = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch?institution=UVA01"
        search_url = base + field_pattern.format("term", "1{}{}".format(int(year) % 100, num_term))
        search_url += field_pattern.format("subject", subject)
        search_url += field_pattern.format("instructor_name", instructor)

        test_response = send_request(year, num_term, subject, instructor, base)

        self.assertEqual(test_response, []) #should be empty

    def test_add_course_equivalence(self):
        factory = RequestFactory()
        user = User.objects.create_superuser(username='foo', is_superuser=True)
        addDummyCourse(factory, user)

        self.assertEqual(1, Course.objects.all().count())
        self.assertEqual(1, Course.objects.all().count())

    def test_delete_course_equivalence(self):
        factory = RequestFactory()
        user = User.objects.create_superuser(username='foo', is_superuser=True)

        course_id = addDummyCourse(factory, user)
        self.assertEqual(1, Course.objects.all().count())

        request = factory.delete('/schedule/remove-course/1/')
        setupRequest(request, user)

        remove_course(request, course_id)

        self.assertEqual(0, Course.objects.all().count())

    def test_add_to_schedule_equivalence(self):
        factory = RequestFactory()
        user = User.objects.create_superuser(username='foo', is_superuser=True)
        course_id = addDummyCourse(factory, user)
        self.assertEqual(1, Course.objects.all().count())

        request = factory.get("/schedule/add-to-schedule/<int:course_id>/")
        setupRequest(request, user)

        add_to_schedule(request, course_id)

        self.assertEqual(1, Schedule.objects.all().count())
        self.assertEqual(1, ScheduleItem.objects.all().count())
        self.assertEqual(course_id, ScheduleItem.objects.all().values()[0]['course_id'])

    def test_add_to_schedule_error(self):
        factory = RequestFactory()
        user = User.objects.create_superuser(username='foo', is_superuser=True)
        addDummyCourse(factory, user)
        self.assertEqual(1, Course.objects.all().count())

        request = factory.get("/schedule/add-to-schedule/<int:course_id>/")
        setupRequest(request, user)

        with self.assertRaises(Http404):
            add_to_schedule(request, 2) #pass incorrect course_id

        self.assertEqual(0, Schedule.objects.all().count())
        self.assertEqual(0, ScheduleItem.objects.all().count())

    def test_view_schedule(self):
        factory = RequestFactory()
        user = User.objects.create_superuser(username='foo', is_superuser=True)
        course_id = addDummyCourse(factory, user)

        request = factory.get("/schedule/add-to-schedule/<int:course_id>/")
        setupRequest(request, user)

        add_to_schedule(request, course_id)

        self.assertEqual(1, Schedule.objects.all().count())
        self.assertEqual(1, ScheduleItem.objects.all().count())

        request = factory.get("/schedule/view_schedule/")
        setupRequest(request, user)
        response = view_schedule(request)

        self.assertEqual(response.status_code, 200)

    def test_view_cart(self):
        factory = RequestFactory()
        user = User.objects.create_superuser(username='foo', is_superuser=True)
        addDummyCourse(factory, user)

        self.assertEqual(1, Course.objects.all().count())

        request = factory.get("/schedule/view_cart/")
        setupRequest(request, user)
        response = view_cart(request)

        self.assertEqual(response.status_code, 200)

    def test_remove_course_from_schedule(self):
        factory = RequestFactory()
        user = User.objects.create_superuser(username='foo', is_superuser=True)
        course_id = addDummyCourse(factory, user)

        request = factory.get("/schedule/add-to-schedule/<int:course_id>/")
        setupRequest(request, user)

        add_to_schedule(request, course_id)

        self.assertEqual(1, Schedule.objects.all().count())
        self.assertEqual(1, ScheduleItem.objects.all().count())

        request = factory.delete('schedule/remove_schedule_course/1')
        setupRequest(request, user)

        remove_course_from_schedule(request, course_id)

        self.assertEqual(0, ScheduleItem.objects.all().count())

    def test_submit_schedule(self):
        factory = RequestFactory()
        user = User.objects.create_superuser(username='foo', is_superuser=True)
        admin = User.objects.create_superuser(username='glendonchin', is_superuser=True)
        course_id = addDummyCourse(factory, user)

        request = factory.get("/schedule/add-to-schedule/<int:course_id>/")
        setupRequest(request, user)

        add_to_schedule(request, course_id)

        self.assertEqual(1, Schedule.objects.all().count())
        self.assertEqual(1, ScheduleItem.objects.all().count())

        request = factory.post('schedule/submit_schedule')
        setupRequest(request, user)

        submit_schedule(request)
        schedule = Schedule.objects.get(pk=1)

        self.assertTrue(schedule.submitted)

    def test_unsubmit_schedule(self):
        factory = RequestFactory()
        user = User.objects.create_superuser(username='foo', is_superuser=True)
        admin = User.objects.create_superuser(username='glendonchin', is_superuser=True)
        course_id = addDummyCourse(factory, user)

        request = factory.get("/schedule/add-to-schedule/<int:course_id>/")
        setupRequest(request, user)

        add_to_schedule(request, course_id)

        self.assertEqual(1, Schedule.objects.all().count())
        self.assertEqual(1, ScheduleItem.objects.all().count())

        request = factory.post('schedule/unsubmit_schedule')
        setupRequest(request, user)

        unsubmit_schedule(request)
        schedule = Schedule.objects.get(pk=1)

        self.assertFalse(schedule.submitted)



    def test_submissions(self):
        factory = RequestFactory()
        user = User.objects.create_superuser(username='foo', is_superuser=True)
        course_id = addDummyCourse(factory, user)

        request = factory.get("/schedule/add-to-schedule/<int:course_id>/")
        setupRequest(request, user)

        add_to_schedule(request, course_id)
        schedule = Schedule.objects.get(user = user)
        schedule.submitted = True
        schedule.save()

        self.assertEqual(1, Schedule.objects.all().count())
        self.assertEqual(1, ScheduleItem.objects.all().count())

        request = factory.get("/schedule/submissions/")
        setupRequest(request, user)
        response = view_schedule(request)

        self.assertEqual(response.status_code, 200)

    def test_approve_schedule(self):
        factory = RequestFactory()
        user = User.objects.create_superuser(username='foo', is_superuser=True)
        course_id = addDummyCourse(factory, user)

        request = factory.get("/schedule/add-to-schedule/<int:course_id>/")
        setupRequest(request, user)

        add_to_schedule(request, course_id)

        self.assertEqual(1, Schedule.objects.all().count())
        self.assertEqual(1, ScheduleItem.objects.all().count())

        schedule = Schedule.objects.get(pk=1)
        schedule.submitted = True
        schedule.save()

        request = factory.post('schedule/approve-schedule/1')
        setupRequest(request, user)

        approve_schedule(request, 1)

        self.assertTrue(schedule.submitted)
        schedule = Schedule.objects.get(pk=1)
        self.assertEqual('approved', schedule.status)

    def test_deny_schedule(self):
        factory = RequestFactory()
        user = User.objects.create_superuser(username='foo', is_superuser=True)
        course_id = addDummyCourse(factory, user)

        request = factory.get("/schedule/add-to-schedule/<int:course_id>/")
        setupRequest(request, user)

        add_to_schedule(request, course_id)

        self.assertEqual(1, Schedule.objects.all().count())
        self.assertEqual(1, ScheduleItem.objects.all().count())

        schedule = Schedule.objects.get(pk=1)
        schedule.submitted = True
        schedule.save()

        request = factory.post('schedule/deny-schedule/1')
        setupRequest(request, user)

        deny_schedule(request, 1)

        self.assertTrue(schedule.submitted)
        schedule = Schedule.objects.get(pk=1)
        self.assertEqual('denied', schedule.status)

