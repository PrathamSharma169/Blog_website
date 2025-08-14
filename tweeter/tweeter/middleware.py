from django.contrib.auth import logout
from django.urls import reverse

class ForceLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed_paths = [
            reverse('login'),
            reverse('logout'),
            '/signup/',
        ]

        # Skip logout if this is the first request after logging in
        if request.session.get('just_logged_in'):
            request.session.pop('just_logged_in', None)
            return self.get_response(request)

        # Force logout unless path is allowed
        if not any(request.path.startswith(p) for p in allowed_paths):
            if request.user.is_authenticated:
                logout(request)

        return self.get_response(request)
