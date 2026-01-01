# api/auth.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import User

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"
ACCESS_EXPIRE_MINUTES = 60
REFRESH_EXPIRE_DAYS = 7
class CookieJWTAuthentication(JWTAuthentication):
    """
    Authenticate user via cookies.
    Automatically uses refresh token to generate a new access token if access token is missing/expired.
    """
    def authenticate(self, request):
        # Try access token
        raw_access = request.COOKIES.get(ACCESS_COOKIE_NAME)
        if raw_access:
            try:
                validated_token = self.get_validated_token(raw_access)
                user = self.get_user(validated_token)
                return (user, validated_token)
            except Exception:
                # access token invalid/expired, continue to refresh
                pass

        # Try refresh token
        raw_refresh = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if not raw_refresh:
            return None

        try:
            refresh = RefreshToken(raw_refresh)
            user = User.objects.get(id=refresh["user_id"])
        except Exception:
            return None

        # Generate new access token
        new_access = refresh.access_token

        # Attach it to request for middleware to set cookie
        request._request._new_access_token = str(new_access)

        return (user, new_access)
