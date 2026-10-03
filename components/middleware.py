from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings


class RequireLoginMiddleware:
    """
    Middleware that enforces authentication across the entire application.
    Unauthenticated users are strictly restricted to the login page.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        login_url = reverse('login')

        # Static assets, media files, login page, and django admin are exempt
        exempt_paths = [
            login_url,
            settings.STATIC_URL,
            settings.MEDIA_URL,
        ]

        if request.path.startswith('/admin/'):
            return self.get_response(request)

        is_exempt = any(request.path.startswith(p) for p in exempt_paths)

        # Unauthenticated users -> Redirect to login with 'next' parameter
        if not request.user.is_authenticated and not is_exempt:
            return redirect(f"{login_url}?next={request.path}")

        # Authenticated users visiting login page -> Redirect to home
        if request.user.is_authenticated and request.path == login_url:
            return redirect('home')

        return self.get_response(request)
