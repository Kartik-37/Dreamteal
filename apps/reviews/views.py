"""
API Views for Universal Reaction Definitions and Media Reviews.
Strictly separates create (`POST`) and update (`PATCH`) endpoints.
Validates query parameters with proper serializers.
"""

from django.db import IntegrityError, transaction
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response

from apps.reviews.models import MediaReview, ReactionDefinition
from apps.reviews.serializers import MediaReviewSerializer, ReactionDefinitionSerializer


class ReviewMediaQuerySerializer(serializers.Serializer):
    media = serializers.IntegerField(required=False, min_value=1)


class IsReviewOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class ReactionDefinitionListView(generics.ListAPIView):
    """
    GET /api/v1/reviews/reactions/
    Returns active universal qualitative reaction definitions.
    """
    queryset = ReactionDefinition.objects.filter(active=True).order_by('sort_order')
    serializer_class = ReactionDefinitionSerializer
    permission_classes = [permissions.AllowAny]


class MediaReviewListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/reviews/?media=<media_id>
    POST /api/v1/reviews/
    """
    serializer_class = MediaReviewSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        query_serializer = ReviewMediaQuerySerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        media_id = query_serializer.validated_data.get('media')

        qs = MediaReview.objects.select_related('user', 'media_item', 'reaction')
        if media_id:
            qs = qs.filter(media_item_id=media_id)

        # Non-owners only see public reviews
        if not self.request.user.is_authenticated:
            qs = qs.filter(is_public=True)
        else:
            qs = qs.filter(models_q_filter(self.request.user))
        return qs.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                instance = serializer.save(user=request.user)
            headers = self.get_success_headers(serializer.data)
            return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED, headers=headers)
        except IntegrityError:
            return Response(
                {'detail': 'A review already exists for this media item. Use PATCH to update it.'},
                status=status.HTTP_409_CONFLICT
            )


def models_q_filter(user):
    from django.db.models import Q
    return Q(is_public=True) | Q(user=user)


class MediaReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/v1/reviews/<id>/
    PATCH /api/v1/reviews/<id>/
    DELETE /api/v1/reviews/<id>/
    """
    serializer_class = MediaReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsReviewOwnerOrReadOnly]
    queryset = MediaReview.objects.select_related('user', 'media_item', 'reaction')
