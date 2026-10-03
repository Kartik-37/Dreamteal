"""
Serializers for Reviews & Universal Reaction Definitions in DreamTeal.
Strictly adheres to the Zero-Star Rating Policy.
Does NOT output any star ratings, scores, or emoji/icons.
"""

from rest_framework import serializers
from apps.reviews.models import MediaReview, ReactionDefinition


COLOR_TOKEN_MAP = {
    'peak': 'electric-gold',
    'loved_it': 'warm-coral',
    'good_time': 'radiant-teal',
    'not_my_thing': 'muted-lavender',
    'skip': 'crimson',
}


class ReactionDefinitionSerializer(serializers.ModelSerializer):
    """
    Universal qualitative reaction badge definition serializer.
    Identified strictly through text labels and dedicated color design tokens.
    """
    color_token = serializers.SerializerMethodField()

    class Meta:
        model = ReactionDefinition
        fields = [
            'id',
            'key',
            'display_name',
            'color_token',
            'description',
            'active',
            'sort_order',
        ]

    def get_color_token(self, obj) -> str:
        return COLOR_TOKEN_MAP.get(obj.key, 'radiant-teal')


class MediaReviewSerializer(serializers.ModelSerializer):
    """
    Qualitative user review serializer.
    Represents: "This is how I feel about this media."
    Separated from diary consumption logs.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    reaction_detail = ReactionDefinitionSerializer(source='reaction', read_only=True)

    class Meta:
        model = MediaReview
        fields = [
            'id',
            'user',
            'username',
            'media_item',
            'reaction',
            'reaction_detail',
            'review_text',
            'contains_spoilers',
            'is_public',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = validated_data.pop('user', getattr(self.context.get('request'), 'user', None))
        return MediaReview.objects.create(user=user, **validated_data)
