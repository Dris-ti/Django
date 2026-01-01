from django.utils.deprecation import MiddlewareMixin
from api.auth import ACCESS_COOKIE_NAME, ACCESS_EXPIRE_MINUTES
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.response import Response

class RefreshAccessTokenMiddleware(MiddlewareMixin):
    """
    Middleware to intercept responses and attach a new JWT access token via an HTTP-only cookie.

    @description
    This middleware monitors the `request` object for a transient attribute `_new_access_token`.
    When found (typically set by a custom authentication backend or a refresh view), 
    it automatically injects a `Set-Cookie` header into the outgoing HTTP response. 
    This ensures that the frontend client receives the updated token without manual 
    extraction from the response body, enhancing security against XSS by using httpOnly flags.

    @initialization
    :param get_response: The next middleware or view in the Django request/response lifecycle.

    @process_response
    :param request: The incoming HttpRequest object (checked for `_new_access_token`).
    :param response: The outgoing HttpResponse/Response object to be modified.
    :return: The modified response object containing the security cookie.

    @example
    # In a View or Authentication Backend:
    request._new_access_token = "eyJhbGciOiJIUzI1NiIsInR..."
    return Response({"detail": "Auth Success"})
    
    # The Middleware will automatically add:
    # Set-Cookie: access_token=...; HttpOnly; Secure; SameSite=None; Max-Age=3600

    @input_arguments
    - ACCESS_COOKIE_NAME: String (e.g., 'access_token')
    - ACCESS_EXPIRE_MINUTES: Integer (e.g., 60)
    - request._new_access_token: String (The raw JWT string)

    @possible_values
    - samesite: 'None' (Cross-site requests), 'Lax' (Standard), 'Strict' (Same-domain only)
    - secure: True (Requires HTTPS), False (Development only)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def process_response(self, request, response):
        """
        Logic executed on the way out of the server.
        """
        # Retrieve the token if it was attached to the request during the cycle
        new_access = getattr(request, "_new_access_token", None)
        
        if new_access:
            # Check if we are in production to set 'secure' dynamically
            is_production = not settings.DEBUG
            
            response.set_cookie(
                key=ACCESS_COOKIE_NAME,
                value=new_access,
                httponly=True,            # Prevents JavaScript from accessing the token (XSS Protection)
                secure=True,              # Ensures cookie is sent only over HTTPS
                samesite='None',          # Required for cross-site (CORS) setups
                max_age=ACCESS_EXPIRE_MINUTES * 60  # Conversion to seconds
            )
            
        return response