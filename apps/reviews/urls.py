"""
URL Configuration for Reviews and Universal Reaction Definitions.
"""

from django.urls import path
from .views import (
    MediaReviewDetailView, MediaReviewListCreateView,
    ReactionDefinitionListView
)

urlpatterns = [
    path('reviews/reactions/', ReactionDefinitionListView.as_view(), name='reaction-list'),
    path('reviews/', MediaReviewListCreateView.as_view(), name='review-list-create'),
    path('reviews/<uuid:pk>/', MediaReviewDetailView.as_view(), name='review-detail'),
]
