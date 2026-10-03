"""
URL Configuration for User Authentication and Profile.
"""

from django.urls import path
from .views import CSRFTokenView, LoginView, LogoutView, MeView

urlpatterns = [
    path('users/csrf/', CSRFTokenView.as_view(), name='user-csrf'),
    path('users/login/', LoginView.as_view(), name='user-login'),
    path('users/logout/', LogoutView.as_view(), name='user-logout'),
    path('users/me/', MeView.as_view(), name='user-me'),
]
