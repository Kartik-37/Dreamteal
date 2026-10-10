"""
URL Routing for Recommendations in DreamTeal.
"""

from django.urls import path
from apps.recommendations.views import RecommendationNextView

urlpatterns = [
    path('recommendations/next/<slug:slug>/', RecommendationNextView.as_view(), name='recommendation-next'),
]
