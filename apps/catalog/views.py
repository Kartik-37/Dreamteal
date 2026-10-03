"""
Views and API Endpoints for Media Catalog in DreamTeal.
Provides:
- Media browsing and detail retrieval with validated query parameters
- Unified local + third-party candidate search with balanced interleaving
- Multi-mode discovery feeds (popular, latest, trending, upcoming)
- Catalog on-demand import with safe cross-provider deduplication and proper HTTP status codes (201 / 200)
- Data-driven external provider attribution
"""

import logging
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import ExternalProvider, MediaItem
from apps.catalog.providers.registry import registry
from apps.catalog.serializers import (
    DiscoveryQuerySerializer, ExternalProviderSerializer,
    MediaImportRequestSerializer, MediaItemDetailSerializer,
    MediaItemListSerializer, MediaListQuerySerializer,
    MediaSearchQuerySerializer
)

logger = logging.getLogger(__name__)


class MediaItemListView(generics.ListAPIView):
    """
    GET /api/v1/media/
    Lists media items with category, genre, tag, ordering, and search filtering.
    Validates query parameters with MediaListQuerySerializer.
    """
    serializer_class = MediaItemListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        query_serializer = MediaListQuerySerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data

        qs = MediaItem.objects.all().prefetch_related('genres', 'tags')

        category = params.get('category') or params.get('media_type')
        if category:
            qs = qs.filter(media_type=category.upper())

        genre_slug = params.get('genre')
        if genre_slug:
            qs = qs.filter(genres__slug=genre_slug)

        tag_slug = params.get('tag')
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)

        search_query = params.get('search') or params.get('q')
        if search_query:
            qs = qs.filter(
                Q(title__icontains=search_query) | Q(synopsis__icontains=search_query)
            )

        ordering = params.get('ordering', '-release_year')
        qs = qs.order_by(ordering)

        return qs.distinct()


class MediaItemDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/media/<slug>/
    Retrieves full details for a media item, including category-specific extensions and provider mappings.
    """
    serializer_class = MediaItemDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        return MediaItem.objects.select_related(
            'movie_detail', 'series_detail', 'manga_detail', 'game_detail'
        ).prefetch_related('genres', 'tags', 'external_mappings__provider')


class MediaImportView(APIView):
    """
    POST /api/v1/media/import/
    Imports external media metadata into DreamTeal's catalog or returns the existing record.
    Returns:
        201 Created for new media items
        200 OK for existing / updated records
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, *args, **kwargs):
        serializer = MediaImportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        provider_key = data['provider'].lower()
        external_id = data['external_id']
        media_type = data.get('media_type') or None
        force_refresh = data.get('force_refresh', False)

        try:
            media_item, created = registry.import_media(
                provider_key=provider_key,
                external_id=external_id,
                media_type=media_type,
                force_refresh=force_refresh
            )
            # Full detail representation
            detail_serializer = MediaItemDetailSerializer(media_item)
            http_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(detail_serializer.data, status=http_status)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Media import failed: %s", str(e), exc_info=True)
            return Response({'error': 'Failed to import external media item.'}, status=status.HTTP_502_BAD_GATEWAY)


class MediaSearchView(APIView):
    """
    GET /api/v1/media/search/?q=<query>&category=<cat>&limit=<int>
    Searches external providers and enriches results with local DreamTeal import status.
    Validates query parameters with MediaSearchQuerySerializer.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        query_serializer = MediaSearchQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data

        query = params.get('q', '').strip()
        if not query:
            return Response({'results': []})

        category = params.get('category')
        limit = params.get('limit', 20)

        # Query provider registry with balanced multi-media search
        candidate_results = registry.search(query=query, category=category, limit=limit)
        results_data = [r.to_dict() for r in candidate_results]

        return Response({'results': results_data})


class DiscoveryView(APIView):
    """
    GET /api/v1/discovery/<category>/?mode=<popular|latest|trending|upcoming>&limit=<int>
    Returns provider-backed discovery feeds (movies, series, manga, manhwa, games).
    Validates query parameters with DiscoveryQuerySerializer.
    """
    permission_classes = [AllowAny]

    def get(self, request, category: str, *args, **kwargs):
        query_serializer = DiscoveryQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data

        mode = params.get('mode', 'popular').lower()
        limit = params.get('limit', 20)

        cat_clean = category.rstrip('s').upper()
        if cat_clean == 'MOVIE':
            resolved_cat = 'MOVIE'
        elif cat_clean in ['SERIE', 'TV']:
            resolved_cat = 'SERIES'
        elif cat_clean == 'MANGA':
            resolved_cat = 'MANGA'
        elif cat_clean == 'MANHWA':
            resolved_cat = 'MANHWA'
        elif cat_clean == 'GAME':
            resolved_cat = 'GAME'
        else:
            return Response(
                {'error': f"Unknown discovery category '{category}'. Supported: movies, series, manga, manhwa, games."},
                status=status.HTTP_400_BAD_REQUEST
            )

        items = registry.discover(resolved_cat, mode=mode, limit=limit)
        return Response({'results': [it.to_dict() for it in items]})


class ExternalProviderListView(generics.ListAPIView):
    """
    GET /api/v1/catalog/providers/
    Lists active metadata providers and data-driven legal attribution notices.
    """
    queryset = ExternalProvider.objects.filter(active=True)
    serializer_class = ExternalProviderSerializer
    permission_classes = [AllowAny]
