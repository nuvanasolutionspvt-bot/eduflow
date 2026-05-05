from django.core.exceptions import ObjectDoesNotExist


class SchoolMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.school = None
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            try:
                profile = getattr(user, 'tenant_profile', None)
            except ObjectDoesNotExist:
                profile = None

            if profile is not None and profile.school is not None:
                request.school = profile.school
            else:
                request.school = getattr(user, 'school', None)
        return self.get_response(request)
