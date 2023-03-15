from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User


# Create your tests here.
class Test_LoginAuthentication(TestCase):
    def test_admin_login(self):
        user = User.objects.create(username='foo', is_superuser=True)
        factory = RequestFactory()

        request = factory.delete('/')
        request.user = user

        permission = user.has_perm('global_permissions.is_advisor')

        self.assertTrue(permission)
