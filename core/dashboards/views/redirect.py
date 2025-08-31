"""
Dashboard redirect views
"""

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse


@login_required
def dashboard_redirect(request):
    """Redirect user đến dashboard phù hợp với role"""

    # Lấy user role
    try:
        user_role = request.user.profile.role  # role đã là string
    except:
        user_role = None

    # Redirect based on role
    if user_role == 'student':
        return redirect('/dashboard/student/')
    elif user_role == 'teacher':
        return redirect('/dashboard/teacher/')
    elif user_role == 'admin' or request.user.is_superuser:
        return redirect('/dashboard/admin/')
    else:
        # Default fallback - có thể redirect đến trang profile để setup role
        return redirect('/profile/')
 