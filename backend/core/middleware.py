from django.conf import settings
from django.http import JsonResponse


class TrustedFrontendWriteMiddleware:
    """Protect API write requests with an explicit trusted-origin check.

    The React frontend and Django API are separate HTTPS origins on Render.
    SessionAuthentication is still used for identity, while unsafe API
    methods are allowed to bypass Django's token-based CSRF check only after
    the browser Origin has been verified against the configured frontend
    origin(s).
    """

    SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS', 'TRACE'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/') and request.method not in self.SAFE_METHODS:
            origin = request.headers.get('Origin')
            trusted = set(getattr(settings, 'CORS_ALLOWED_ORIGINS', []))
            if origin and origin in trusted:
                request._dont_enforce_csrf_checks = True
            else:
                return JsonResponse(
                    {'error': 'Untrusted request origin.'},
                    status=403,
                )
        return self.get_response(request)
