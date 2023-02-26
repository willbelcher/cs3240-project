from django.shortcuts import render
# Create your views here.
def post_list(request):
    user = request.user
    role = ""
    username = user.username
    if user.has_perm('global_permissions.is_advisor'):
        role = "Advisor"
    else:
        role = "Student"
    return render(request, 'schedule/post_list.html', {'role': role, 'username': username})
