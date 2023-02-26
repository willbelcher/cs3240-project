from django.shortcuts import render
# Create your views here.
def post_list(request):
    user = request.user
    if user.has_perm('global_permissions.is_advisor'):
        return render(request, 'schedule/post_list.html', {})
    else:
        return render(request, 'schedule/student_post_list.html', {})
