from functools import wraps
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied


def portal_permission(permission):
    def decorator(view):
        @staff_member_required(login_url="admin:login")
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.has_perm(permission):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
