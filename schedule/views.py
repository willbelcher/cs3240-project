from django.shortcuts import render

# Create your views here.
def post_list(request):
    return render(request, 'schedule/post_list.html', {})

def login(request):
    return render(request, 'schedule/login.html', {})
