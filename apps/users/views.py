"""
API Views for User Authentication (Session + CSRF) and Profile Management.
"""

from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers import LoginSerializer, UserMeSerializer, UserProfileSerializer


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFTokenView(APIView):
    """
    GET /api/v1/users/csrf/
    Ensures the CSRF cookie is set and returns the token for client state initialization.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        token = get_token(request)
        return Response({'csrftoken': token})


class LoginView(APIView):
    """
    POST /api/v1/users/login/
    Authenticates user credentials and establishes a Django session.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response(
            {'user': UserMeSerializer(user).data, 'detail': 'Successfully authenticated.'},
            status=status.HTTP_200_OK
        )


class LogoutView(APIView):
    """
    POST /api/v1/users/logout/
    Flushes the active session cookie.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)


class MeView(APIView):
    """
    GET /api/v1/users/me/
    PATCH /api/v1/users/me/
    Retrieves or updates the current authenticated user profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserMeSerializer(request.user).data)
