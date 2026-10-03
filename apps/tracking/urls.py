"""
URL Configuration for User Tracking, Progress, and Diary Logs.
"""

from django.urls import path
from .views import (
    DiaryLogDetailView, DiaryLogListCreateView,
    UserMediaProgressDetailView, UserMediaProgressListCreateView,
    UserMediaStatusDetailView, UserMediaStatusListCreateView
)

urlpatterns = [
    # Status endpoints
    path('tracking/status/', UserMediaStatusListCreateView.as_view(), name='status-list-create'),
    path('tracking/status/<uuid:pk>/', UserMediaStatusDetailView.as_view(), name='status-detail'),

    # Progress endpoints
    path('tracking/progress/', UserMediaProgressListCreateView.as_view(), name='progress-list-create'),
    path('tracking/progress/<uuid:pk>/', UserMediaProgressDetailView.as_view(), name='progress-detail'),

    # Diary log endpoints
    path('tracking/logs/', DiaryLogListCreateView.as_view(), name='diary-list-create'),
    path('tracking/logs/<uuid:pk>/', DiaryLogDetailView.as_view(), name='diary-detail'),
]
