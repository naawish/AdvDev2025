from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test

def role_required(allowed_roles=[]):
    """
    Decorator for views that checks whether a user has one of the allowed roles.
    """
    def check_role(user):
        if user.is_authenticated and user.role in allowed_roles:
            return True
        raise PermissionDenied # Or return False to let user_passes_test handle redirect
    return user_passes_test(check_role)

# Example Usage in views.py:
# from .decorators import role_required
#
# @login_required
# @role_required(['MANAGER', 'ADMIN'])
# def some_manager_or_admin_view(request):
#     # ... view logic ...