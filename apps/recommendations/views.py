"""
API Views for In-House Recommendations in DreamTeal.
Adheres strictly to the Zero-Star Rating Policy.
Provides explainable "What to consume next" suggestions.
"""

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import MediaItem
from apps.recommendations.serializers import (
    RecommendationQuerySerializer,
    RecommendationResponseSerializer
)
from apps.recommendations.services import RecommendationEngine


class RecommendationNextView(APIView):
    """
    GET /api/v1/recommendations/next/<slug>/
    Returns deterministic, explainable recommendations for what to watch, read, or play next.
    Supports anonymous discovery and authenticated personalized filtering.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug: str, *args, **kwargs):
        # 1. Fetch base media item or return 404
        source_item = get_object_or_404(
            MediaItem.objects.select_related(
                'movie_detail', 'series_detail', 'manga_detail', 'game_detail'
            ).prefetch_related('genres', 'tags'),
            slug=slug
        )

        # 2. Validate query parameters (returns 400 Bad Request on invalid input)
        query_serializer = RecommendationQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data

        cross_category = params.get('cross_category', True)
        category = params.get('category')
        limit = params.get('limit', 10)
        include_scores = params.get('include_scores', False)

        # 3. Compute recommendations via deterministic engine
        engine = RecommendationEngine()
        user = request.user if request.user.is_authenticated else None
        recommendations = engine.get_recommendations(
            source_item=source_item,
            user=user,
            cross_category=cross_category,
            target_category=category,
            limit=limit
        )

        # 4. Serialize envelope response
        payload = {
            'base_media': source_item,
            'recommendations': recommendations,
            'count': len(recommendations),
            'filters': {
                'cross_category': cross_category,
                'category': category.upper() if category else None,
                'limit': limit,
            }
        }
        serializer = RecommendationResponseSerializer(
            payload,
            context={'include_scores': include_scores}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
