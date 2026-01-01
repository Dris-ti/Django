# api/auth.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import User

# Configuration Constants
ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"
ACCESS_EXPIRE_MINUTES = 60
REFRESH_EXPIRE_DAYS = 7

class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom Authentication Backend for seamless JWT session management via Cookies.

    @description
    This class overrides standard JWT authentication to prioritize HTTP-only cookies over 
    Authorization headers. It implements a 'Self-Healing' session logic: if an access 
    token is expired but a valid refresh token exists, it transparently generates a 
    new access token and attaches it to the request. This avoids 401 errors on the frontend.

    @returns
    - Tuple: (User object, validated_token) if successful.
    - None: If no valid authentication method is found.

    @side_effects
    - Injects `request._new_access_token`: When a refresh occurs, this attribute 
      is used by `RefreshAccessTokenMiddleware` to update the client's cookie.

    @example
    # Request arrives with expired access_token and valid refresh_token:
    # 1. authenticate() fails access check.
    # 2. authenticate() succeeds refresh check.
    # 3. New access_token generated.
    # 4. Request proceeds to View as authenticated.

    @input_arguments
    - ACCESS_COOKIE_NAME: str
    - REFRESH_COOKIE_NAME: str

    @possible_errors
    - User.DoesNotExist: If a token exists for a deleted user.
    - TokenError: If the refresh token is blacklisted or tampered with.
    """
    def authenticate(self, request):
        """
        Main authentication entry point.
        """
        # Step 1: Validate Access Token from Cookie
        raw_access = request.COOKIES.get(ACCESS_COOKIE_NAME)
        if raw_access:
            try:
                validated_token = self.get_validated_token(raw_access)
                user = self.get_user(validated_token)
                return (user, validated_token)
            except Exception:
                # Access token is stale or invalid; fall back to Refresh logic
                pass

        # Step 2: Validate Refresh Token from Cookie
        raw_refresh = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if not raw_refresh:
            return None

        try:
            # Step 3: Attempt Refresh
            refresh = RefreshToken(raw_refresh)
            user = User.objects.get(id=refresh["user_id"])
            
            # Step 4: Generate New Access Token
            new_access = refresh.access_token

            # Step 5: Secure Hand-off to Middleware
            # We use request._request because DRF wraps the standard Django request
            request._request._new_access_token = str(new_access)

            return (user, new_access)
            
        except Exception:
            # Refresh token is also expired or invalid
            return None