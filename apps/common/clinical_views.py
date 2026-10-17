"""Session-authenticated access for the legacy clinical views."""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from apps.accounts.models import UserRole


def clinical_view(view):
    @login_required
    @wraps(view)
    def protected(request, *args, **kwargs):
        allowed = {UserRole.ADMIN, UserRole.NEUROPSYCHOLOGIST, UserRole.ASSISTANT}
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            allowed |= {UserRole.REVIEWER, UserRole.READONLY}
        if request.user.role not in allowed:
            return JsonResponse({"message": "Permissão negada."}, status=403)
        return view(request, *args, **kwargs)

    return protected
