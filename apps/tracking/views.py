"""
API Views for User Media Status, Progress Tracking, and History-Preserving Diary Logs.
Strictly separates create (`POST`) and update (`PATCH`) endpoints.
Validates all query parameters to prevent 500 errors on invalid inputs.
"""

from django.db import IntegrityError, transaction
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response

from apps.tracking.models import DiaryLog, UserMediaProgress, UserMediaStatus
from apps.tracking.serializers import (
    DiaryLogSerializer, UserMediaProgressSerializer, UserMediaStatusSerializer
)


class TrackingMediaQuerySerializer(serializers.Serializer):
    media = serializers.IntegerField(required=False, min_value=1)


class DiaryLogFilterSerializer(serializers.Serializer):
    media = serializers.IntegerField(required=False, min_value=1)
    year = serializers.IntegerField(required=False, min_value=1900, max_value=2100)
    month = serializers.IntegerField(required=False, min_value=1, max_value=12)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object-level permission allowing only the owner to edit or delete."""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class UserMediaStatusListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/tracking/status/?media=<id>
    POST /api/v1/tracking/status/
    """
    serializer_class = UserMediaStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query_serializer = TrackingMediaQuerySerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        media_id = query_serializer.validated_data.get('media')

        qs = UserMediaStatus.objects.filter(user=self.request.user)
        if media_id:
            qs = qs.filter(media_item_id=media_id)
        return qs

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
                {'detail': 'A status already exists for this media item. Use PATCH to update it.'},
                status=status.HTTP_409_CONFLICT
            )


class UserMediaStatusDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/v1/tracking/status/<id>/
    PATCH /api/v1/tracking/status/<id>/
    DELETE /api/v1/tracking/status/<id>/
    Strictly scoped to the authenticated user.
    """
    serializer_class = UserMediaStatusSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return UserMediaStatus.objects.filter(user=self.request.user)


class UserMediaProgressListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/tracking/progress/?media=<id>
    POST /api/v1/tracking/progress/
    """
    serializer_class = UserMediaProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query_serializer = TrackingMediaQuerySerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        media_id = query_serializer.validated_data.get('media')

        qs = UserMediaProgress.objects.filter(user=self.request.user).select_related(
            'series_progress', 'manga_progress', 'game_progress'
        )
        if media_id:
            qs = qs.filter(media_item_id=media_id)
        return qs

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
                {'detail': 'Progress already exists for this media item. Use PATCH to update it.'},
                status=status.HTTP_409_CONFLICT
            )


class UserMediaProgressDetailView(generics.RetrieveUpdateAPIView):
    """
    GET /api/v1/tracking/progress/<id>/
    PATCH /api/v1/tracking/progress/<id>/
    Strictly scoped to the authenticated user.
    """
    serializer_class = UserMediaProgressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return UserMediaProgress.objects.filter(user=self.request.user).select_related(
            'series_progress', 'manga_progress', 'game_progress'
        )


class DiaryLogListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/tracking/logs/?media=<id>&year=<year>&month=<month>
    POST /api/v1/tracking/logs/
    """
    serializer_class = DiaryLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query_serializer = DiaryLogFilterSerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data

        qs = DiaryLog.objects.filter(user=self.request.user).select_related('media_item')
        media_id = params.get('media')
        if media_id:
            qs = qs.filter(media_item_id=media_id)

        year = params.get('year')
        if year:
            qs = qs.filter(logged_date__year=year)

        month = params.get('month')
        if month:
            qs = qs.filter(logged_date__month=month)

        return qs.order_by('-logged_date', '-created_at')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(user=request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED, headers=headers)


class DiaryLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/v1/tracking/logs/<id>/
    PATCH /api/v1/tracking/logs/<id>/
    DELETE /api/v1/tracking/logs/<id>/
    Controlled editing of a specific historical diary record without affecting others.
    Strictly scoped to the authenticated user.
    """
    serializer_class = DiaryLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return DiaryLog.objects.filter(user=self.request.user).select_related('media_item')
