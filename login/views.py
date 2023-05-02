from allauth.account.utils import get_next_redirect_url, complete_signup, passthrough_next_redirect_url
from allauth.account.views import RedirectAuthenticatedUserMixin, CloseableSignupMixin, AjaxCapableProcessFormViewMixin
from allauth.decorators import rate_limit
from allauth.exceptions import ImmediateHttpResponse
from allauth.utils import get_form_class, get_request_param
from allauth.account import app_settings
from .forms import SignupForm
from allauth.account.adapter import get_adapter

from django.contrib.sites.shortcuts import get_current_site
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.views.generic.edit import FormView
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.models import Group

sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters("oldpassword", "password", "password1", "password2")
)


# Create your views here.
def login(request):
    user = request.user
    if user.is_authenticated:
        return HttpResponseRedirect('schedule/')  # no need to login, just jump to home page
    else:
        # return render(request, 'login/login.html', {})
        return render(request, 'account/login.html', {})


@method_decorator(rate_limit(action="signup"), name="dispatch")
class SignupView(
    RedirectAuthenticatedUserMixin,
    CloseableSignupMixin,
    AjaxCapableProcessFormViewMixin,
    FormView,
):
    template_name = "account/signup." + app_settings.TEMPLATE_EXTENSION
    form_class = SignupForm
    redirect_field_name = "next"
    success_url = None
    global_wants_advisor = False

    @sensitive_post_parameters_m
    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":

            fields = request.POST.copy()
            wants_advisor = fields.get('permissions')

            if wants_advisor == 'advisor':
                self.global_wants_advisor = True
            else:
                self.global_wants_advisor = False

        return super(SignupView, self).dispatch(request, *args, **kwargs)

    def get_form_class(self):
        return get_form_class(app_settings.FORMS, "signup", self.form_class)

    def get_success_url(self):
        # Explicitly passed ?next= URL takes precedence
        ret = (
                get_next_redirect_url(self.request, self.redirect_field_name)
                or self.success_url
        )
        return ret

    def form_valid(self, form):
        self.user = form.save(self.request)

        if not self.user:
            return get_adapter(self.request).respond_email_verification_sent(
                self.request, None
            )
        try:
            if self.global_wants_advisor:
                advisor_group = Group.objects.get(name='Advisor')
                self.user.groups.add(advisor_group)
            else:
                student_group = Group.objects.get(name='Student')
                self.user.groups.add(student_group)
            return complete_signup(
                self.request,
                self.user,
                app_settings.EMAIL_VERIFICATION,
                self.get_success_url(),
            )
        except ImmediateHttpResponse as e:
            return e.response

    def get_context_data(self, **kwargs):
        ret = super(SignupView, self).get_context_data(**kwargs)
        form = ret["form"]
        email = self.request.session.get("account_verified_email")
        if email:
            email_keys = ["email"]
            if app_settings.SIGNUP_EMAIL_ENTER_TWICE:
                email_keys.append("email2")
            for email_key in email_keys:
                form.fields[email_key].initial = email
        login_url = passthrough_next_redirect_url(
            self.request, reverse("account_login"), self.redirect_field_name
        )
        redirect_field_name = self.redirect_field_name
        site = get_current_site(self.request)
        redirect_field_value = get_request_param(self.request, redirect_field_name)
        ret.update(
            {
                "login_url": login_url,
                "redirect_field_name": redirect_field_name,
                "redirect_field_value": redirect_field_value,
                "site": site,
            }
        )
        return ret


signup = SignupView.as_view()
