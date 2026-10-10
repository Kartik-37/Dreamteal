"""
Serializers and Query Parameter Validators for Recommendations in DreamTeal.
Strictly adheres to the Zero-Star Rating Policy.
"""

from rest_framework import serializers
from apps.catalog.models import MediaItem


class RecommendationQuerySerializer(serializers.Serializer):
    """
    Validates query parameters for GET /api/v1/recommendations/next/<slug>/
    Returns 400 Bad Request on invalid inputs.
    """
    cross_category = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Allow recommendations from other media categories (default true)."
    )
    category = serializers.ChoiceField(
        choices=['MOVIE', 'SERIES', 'MANGA', 'MANHWA', 'GAME', 'movie', 'series', 'manga', 'manhwa', 'game'],
        required=False,
        allow_null=True,
        help_text="Optional explicit target category filter."
    )
    limit = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=50,
        help_text="Maximum number of recommendations to return (1-50, default 10)."
    )
    include_scores = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Development diagnostic flag to include internal scores in responses."
    )


class RecommendationBaseMediaSerializer(serializers.ModelSerializer):
    """Summarized source media representation."""
    class Meta:
        model = MediaItem
        fields = ['id', 'slug', 'title', 'media_type']


class RecommendedItemSerializer(serializers.Serializer):
    """Individual recommended candidate representation with explainable match reasons."""
    id = serializers.UUIDField(source='candidate.id')
    slug = serializers.CharField(source='candidate.slug')
    title = serializers.CharField(source='candidate.title')
    media_type = serializers.CharField(source='candidate.media_type')
    poster_url = serializers.CharField(source='candidate.poster_url')
    release_year = serializers.IntegerField(source='candidate.release_year', allow_null=True)
    match_reasons = serializers.ListField(child=serializers.CharField())
    similarity_score = serializers.FloatField(source='total_score', required=False)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Suppress internal similarity_score unless specifically requested in diagnostic context
        include_scores = self.context.get('include_scores', False)
        if not include_scores:
            data.pop('similarity_score', None)
        return data


class RecommendationResponseSerializer(serializers.Serializer):
    """Envelope response serializer for GET /api/v1/recommendations/next/<slug>/."""
    base_media = RecommendationBaseMediaSerializer()
    recommendations = RecommendedItemSerializer(many=True)
    count = serializers.IntegerField()
    filters = serializers.DictField()
