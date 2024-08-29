import functools

from django.http import HttpResponseForbidden


def group_required(group_name):
    def decorator(view):
        @functools.wraps(view)
        def wrapper(request, *args, **kwargs):
            if (request.user.groups.filter(name=group_name).exists() or
                    request.user.is_superuser):
                return view(request, *args, **kwargs)
            else:
                return HttpResponseForbidden("You don't have permission to view this page.")
        return wrapper
    return decorator