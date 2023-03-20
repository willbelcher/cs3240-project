import requests
from django.test import TestCase, RequestFactory, Client
from schedule.views import send_request
from rest_framework.test import APITestCase

from django.contrib.auth.models import User, Group, Permission

# Create your tests here.
class TestCourseSearch(APITestCase):
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
