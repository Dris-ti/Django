from django.utils.deprecation import MiddlewareMixin
from api.auth import ACCESS_COOKIE_NAME, ACCESS_EXPIRE_MINUTES
from django.conf import settings


class RefreshAccessTokenMiddleware(MiddlewareMixin):
    """
    If authentication created a new access token, automatically set it in httpOnly cookie.
    """
    def process_response(self, request, response):
        new_access = getattr(request, "_new_access_token", None)
        if new_access:
            response.set_cookie(
                ACCESS_COOKIE_NAME,
                new_access,
                httponly=True,
                secure=True,        # True in production
                samesite='None',
                max_age=ACCESS_EXPIRE_MINUTES * 60
            )
        return response
