from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from api.models import  User
import bcrypt
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from api.auth import CookieJWTAuthentication
from api.utils.encode import  encode_response
from api.auth import ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME, ACCESS_EXPIRE_MINUTES, REFRESH_EXPIRE_DAYS


def set_cookie(response, key, value, max_age):
    response.set_cookie(
        key,
        value,
        httponly=True,
        secure=True,       # True in production (HTTPS)
        samesite='None',
        max_age=max_age
    )

def delete_cookie(response, key):
    response.delete_cookie(
        key=key,
        path="/",
        samesite="None"
    )


# Create your views here.
@api_view(['POST'])
@permission_classes([AllowAny])
def sign_up(request):
    if request.method != 'POST':
        return Response({"error": "POST method required"}, status=405)
    
    try:
        name = request.data.get("name")
        email = request.data.get("email")
        password = request.data.get("password")
        if not name:
            return Response({"error": "Name is required"}, status=400)
        
        if not email:
            return Response({"error": "Email is required"}, status=400)
        
        if not password:
            return Response({"error": "Password is required"}, status=400)
        
        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=409)
        
        user = User(email=email, username=email, name=name)
        user.set_password(password)
        user.save()
        return Response(encode_response({"message": "User created successfully"}, status=201))
    
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# @api_view(['POST'])
# @permission_classes([AllowAny])
# def login(request):
#     if request.method != 'POST':
#         return Response({"error": "POST method required"}, status=405)
    
#     try:
#         email = request.data.get("email")

#         print(email)

#         if not email:
#             return Response({"error": "Email is required"}, status=400)
#         print("I am here ")
    
        
#         print("I am here 2")
       
#         user = authenticate(request, email=email, )
            
#         if not user:
#             return Response({"error": "Invalid credentials"}, status=401)
       

        
#         print("I am here 5")
#         refresh = RefreshToken.for_user(user)
#         response = Response(encode_response({
#             "access": str(refresh.access_token),
#             "refresh": str(refresh),
#             "user": {"id": user.id, "email": user.email, "name": user.name}
#         }))
        
#         # HttpOnly cookies
#         response.set_cookie(
#             key="access_token",
#             value=str(refresh.access_token),
#             httponly=True,
#             secure=True,      # True in production (HTTPS)
#             samesite="None",
#             max_age=15 * 60,
#         )

#         response.set_cookie(
#             key="refresh_token",
#             value=str(refresh),
#             httponly=True,
#             secure=True,
#             samesite="None",
#             max_age=24 * 60 * 60,
#         )
#         print("I am here 6")
#         return response
    
#     except Exception as e:
#         return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    if request.method != "POST":
        return Response({"error": "POST required"}, status=400)

    email = request.data.get("email")
    if not email:
        return Response({"error": "Email required"}, status=400)

    try:
        print("Found")
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        print("Not found")
        response = Response(
        {"error": "User not found"},
        status=404
        )
        delete_cookie(response, ACCESS_COOKIE_NAME)
        delete_cookie(response, REFRESH_COOKIE_NAME)
        return response

    # Generate tokens
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    response = Response(encode_response({"message": "Login successful"}))
    set_cookie(response, ACCESS_COOKIE_NAME, str(access), 10*60)        # 10 min
    set_cookie(response, REFRESH_COOKIE_NAME, str(refresh), 7*24*60*60) # 7 days
    print("Not found 2")
    return response
 
@permission_classes([AllowAny])
def refresh(request):
    refresh_token = request.COOKIES.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        return Response({"error": "No refresh token"}, status=401)

    try:
        refresh = RefreshToken(refresh_token)
        new_access = refresh.access_token
        new_refresh = refresh.rotate()  # rotates refresh token automatically
    except Exception:
        return Response({"error": "Invalid refresh token"}, status=401)

    response = Response({"message": "Tokens refreshed"})
    set_cookie(response, ACCESS_COOKIE_NAME, str(new_access), ACCESS_EXPIRE_MINUTES*60)
    set_cookie(response, REFRESH_COOKIE_NAME, str(new_refresh), REFRESH_EXPIRE_DAYS*24*60*60)
    return response

@api_view(['POST'])
def logout(request):
    response = Response({"message": "Logged out"})
    response.delete_cookie(ACCESS_COOKIE_NAME)
    response.delete_cookie(REFRESH_COOKIE_NAME)
    return response


@api_view(['GET'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user
    if not user or not user.is_authenticated:
        return Response({"error": "Unauthorized"}, status=401)
    obfuscated = encode_response({
            "email": user.email,
        })
    return Response(obfuscated)

   