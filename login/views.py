from django.http.response import HttpResponseRedirect
from django.shortcuts import render


# Create your views here.
def login(request):
    user = request.user
    if user.is_authenticated:
        return HttpResponseRedirect('schedule/')  # no need to login, just jump to home page
    else:
        # return render(request, 'login/login.html', {})
        return render(request, 'account/login.html', {})






