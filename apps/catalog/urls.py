"""
URL Configuration for Media Catalog, Search, Discovery, and Provider Attribution.
"""

from django.urls import path
from .views import (
    DiscoveryView, ExternalProviderListView, MediaImportView,
    MediaItemDetailView, MediaItemListView, MediaSearchView
)

urlpatterns = [
    # Catalog browsing & details
    path('media/', MediaItemListView.as_view(), name='media-list'),
    path('media/search/', MediaSearchView.as_view(), name='media-search'),
    path('media/import/', MediaImportView.as_view(), name='media-import'),
    path('media/<slug:slug>/', MediaItemDetailView.as_view(), name='media-detail'),

    # Provider Discovery feeds
    path('discovery/<str:category>/', DiscoveryView.as_view(), name='discovery-feed'),

    # Provider attribution
    path('catalog/providers/', ExternalProviderListView.as_view(), name='provider-list'),
]
