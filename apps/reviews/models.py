"""
Reviews & Universal Reactions Models for DreamTeal.

Defines:
- ReactionDefinition: Dynamic, qualitative pop-culture reaction verdicts
  (⚡ Peak, 💎 Loved It, 🍿 Good Time, 🌙 Not My Thing, 🛑 Skip).
  Strictly non-numeric; no star ratings or numerical equivalents.
- MediaReview: User reviews attaching a reaction verdict and written critique.
  Maintains strict entity separation from consumption diary logs.
"""

import uuid
from django.conf import settings
from django.db import models


class ReactionDefinition(models.Model):
    """
    Universal qualitative reaction badge definition for DreamTeal.
    Decoupled from review columns and seeded through controlled seed data.
    Applicable universally across Movies, TV Series, Manga, and Games.
    Identified primarily through typography and dedicated color design tokens.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.SlugField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique slug identifier (e.g., 'peak', 'loved_it', 'good_time', 'not_my_thing', 'skip')."
    )
    display_name = models.CharField(
        max_length=100,
        help_text="Human-readable title (e.g. 'Loved It')."
    )
    description = models.TextField(
        blank=True,
        default='',
        help_text="Editorial explanation of what this qualitative verdict signifies."
    )
    active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Flag to allow enabling/retiring badges gracefully without breaking historical reviews."
    )
    sort_order = models.PositiveIntegerField(
        default=1,
        help_text="Display ordering sequence in picker modals and UI chips."
    )

    class Meta:
        ordering = ['sort_order']
        verbose_name = 'Reaction Definition'
        verbose_name_plural = 'Reaction Definitions'

    def __str__(self):
        return self.display_name


class MediaReview(models.Model):
    """
    Qualitative user review for a media catalog item.
    Represents: "This is how I feel about this media."
    Contains qualitative verdict reaction badge + written markdown commentary.
    Strictly separate from diary consumption history.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='media_reviews'
    )
    media_item = models.ForeignKey(
        'catalog.MediaItem',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    reaction = models.ForeignKey(
        ReactionDefinition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews',
        help_text="Qualitative verdict outcome badge. Strictly non-numeric."
    )
    review_text = models.TextField(
        blank=True,
        default='',
        help_text="Written critique or qualitative impressions (Markdown supported)."
    )
    contains_spoilers = models.BooleanField(
        default=False,
        help_text="Flag controlling spoiler mask overlays in the UI."
    )
    is_public = models.BooleanField(
        default=True,
        help_text="Visibility toggle (True = community visible, False = personal notes)."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Media Review'
        verbose_name_plural = 'Media Reviews'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'media_item'],
                name='unique_user_media_review'
            )
        ]
        indexes = [
            models.Index(fields=['media_item', 'is_public']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        reaction_str = f" [{self.reaction.display_name}]" if self.reaction else ""
        return f"Review by {self.user.username} on {self.media_item.title}{reaction_str}"
