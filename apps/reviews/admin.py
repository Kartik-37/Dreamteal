"""
Django Admin Configuration for Reviews and Universal Reaction Definitions.
"""

from django.contrib import admin
from .models import ReactionDefinition, MediaReview


@admin.register(ReactionDefinition)
class ReactionDefinitionAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'key', 'sort_order', 'active')
    list_editable = ('sort_order', 'active')
    search_fields = ('display_name', 'key', 'description')
    ordering = ('sort_order',)


@admin.register(MediaReview)
class MediaReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'media_item', 'reaction', 'contains_spoilers', 'is_public', 'created_at')
    list_filter = ('reaction', 'contains_spoilers', 'is_public')
    search_fields = ('user__username', 'media_item__title', 'review_text')
