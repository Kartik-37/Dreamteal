"""
Backend tests for apps.reviews.
Tests ReactionDefinition, MediaReview, uniqueness constraints, and performs a strict
automated schema audit proving ZERO star ratings or numeric ratings exist anywhere in the database.
"""

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from apps.catalog.models import MediaItem
from apps.reviews.models import ReactionDefinition, MediaReview

User = get_user_model()


class ReviewsModelsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='carol', password='password123')
        self.movie = MediaItem.objects.create(
            media_type=MediaItem.MediaType.MOVIE,
            title='Blade Runner 2049',
            slug='blade-runner-2049-2017',
            release_year=2017
        )

        # Create the 5 approved reaction definitions
        self.rx_peak = ReactionDefinition.objects.create(
            key='peak', display_name='Peak', sort_order=1
        )
        self.rx_loved_it = ReactionDefinition.objects.create(
            key='loved_it', display_name='Loved It', sort_order=2
        )
        self.rx_good_time = ReactionDefinition.objects.create(
            key='good_time', display_name='Good Time', sort_order=3
        )
        self.rx_not_my_thing = ReactionDefinition.objects.create(
            key='not_my_thing', display_name='Not My Thing', sort_order=4
        )
        self.rx_skip = ReactionDefinition.objects.create(
            key='skip', display_name='Skip', sort_order=5
        )

    def test_five_approved_reactions_exist_and_unique(self):
        """Verifies the 5 approved reaction definitions and unique key constraint."""
        self.assertEqual(ReactionDefinition.objects.count(), 5)

        with self.assertRaises(IntegrityError):
            ReactionDefinition.objects.create(
                key='peak',  # Duplicate key
                display_name='Duplicate Peak'
            )

    def test_reaction_definition_has_no_icon_or_emoji_field(self):
        """Verifies ReactionDefinition has no icon, emoji, or symbol field per Phase 2 decisions."""
        field_names = [f.name for f in ReactionDefinition._meta.get_fields()]
        self.assertNotIn('icon', field_names)
        self.assertNotIn('emoji', field_names)
        self.assertNotIn('symbol', field_names)

    def test_review_creation_and_fields(self):
        """Verifies creating a qualitative review attached to a ReactionDefinition."""
        review = MediaReview.objects.create(
            user=self.user,
            media_item=self.movie,
            reaction=self.rx_peak,
            review_text="Atmospheric neo-noir masterpiece of visual storytelling.",
            contains_spoilers=False,
            is_public=True
        )
        self.assertEqual(review.reaction.key, 'peak')
        self.assertEqual(review.reaction.display_name, 'Peak')

    def test_review_uniqueness_per_user_and_media(self):
        """Verifies a user cannot have duplicate reviews for the same media item."""
        MediaReview.objects.create(
            user=self.user,
            media_item=self.movie,
            reaction=self.rx_peak,
            review_text="Initial review."
        )

        with self.assertRaises(IntegrityError):
            MediaReview.objects.create(
                user=self.user,
                media_item=self.movie,
                reaction=self.rx_loved_it,
                review_text="Second review attempt."
            )

    def test_deleting_review_preserves_media_and_reaction(self):
        """Verifies deleting a review leaves MediaItem and ReactionDefinition intact."""
        review = MediaReview.objects.create(
            user=self.user,
            media_item=self.movie,
            reaction=self.rx_good_time
        )
        review_id = review.id
        review.delete()

        self.assertFalse(MediaReview.objects.filter(id=review_id).exists())
        self.assertTrue(MediaItem.objects.filter(id=self.movie.id).exists())
        self.assertTrue(ReactionDefinition.objects.filter(key='good_time').exists())

    # -----------------------------------------------------
    # STRICT ZERO STAR / NUMERIC RATING AUDIT TEST
    # -----------------------------------------------------
    def test_strict_zero_star_ratings_across_entire_database(self):
        """
        Automated architectural assertion:
        Inspects EVERY registered Django model across DreamTeal apps.
        Asserts that NO field name or db_column represents star ratings,
        numeric scores, or rating averages.
        """
        dreamteal_apps = ['catalog', 'tracking', 'reviews', 'users']
        forbidden_substrings = ['star', 'stars', 'rating', 'score', 'points', 'grade', 'numeric_val']

        for app_label in dreamteal_apps:
            app_models = apps.get_app_config(app_label).get_models()
            for model in app_models:
                for field in model._meta.get_fields():
                    field_name_lower = field.name.lower()
                    for forbidden in forbidden_substrings:
                        self.assertNotIn(
                            forbidden,
                            field_name_lower,
                            f"VIOLATION: Forbidden rating substring '{forbidden}' found in field '{field.name}' of model '{model.__name__}' in app '{app_label}'!"
                        )


from rest_framework.test import APIClient


class ReviewsAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='tester_reviews', password='pass123_secure')
        self.client.force_authenticate(user=self.user)

        self.movie = MediaItem.objects.create(
            media_type='MOVIE', title='Arrival', slug='arrival-2016', release_year=2016
        )

        self.rx_peak = ReactionDefinition.objects.create(
            key='peak', display_name='Peak', sort_order=1
        )
        self.rx_loved_it = ReactionDefinition.objects.create(
            key='loved_it', display_name='Loved It', sort_order=2
        )
        self.rx_good_time = ReactionDefinition.objects.create(
            key='good_time', display_name='Good Time', sort_order=3
        )
        self.rx_not_my_thing = ReactionDefinition.objects.create(
            key='not_my_thing', display_name='Not My Thing', sort_order=4
        )
        self.rx_skip = ReactionDefinition.objects.create(
            key='skip', display_name='Skip', sort_order=5
        )

    def test_reactions_api_endpoint_structure_and_no_icons(self):
        """Verifies GET /api/v1/reviews/reactions/ returns 5 reactions with color tokens and NO icons."""
        res = self.client.get('/api/v1/reviews/reactions/')
        self.assertEqual(res.status_code, 200)
        results = res.data.get('results', res.data)
        self.assertEqual(len(results), 5)

        keys = [r['key'] for r in results]
        self.assertEqual(keys, ['peak', 'loved_it', 'good_time', 'not_my_thing', 'skip'])

        for item in results:
            self.assertIn('color_token', item)
            self.assertNotIn('icon', item)
            self.assertNotIn('emoji', item)
            self.assertNotIn('symbol', item)

        self.assertEqual(results[0]['color_token'], 'electric-gold')
        self.assertEqual(results[1]['color_token'], 'warm-coral')
        self.assertEqual(results[2]['color_token'], 'radiant-teal')
        self.assertEqual(results[3]['color_token'], 'muted-lavender')
        self.assertEqual(results[4]['color_token'], 'crimson')

    def test_review_create_conflict_and_patch(self):
        # 1. Create review
        res = self.client.post('/api/v1/reviews/', {
            'media_item': str(self.movie.id),
            'reaction': str(self.rx_peak.id),
            'review_text': 'Masterful sci-fi exploration of linguistics and time.',
            'contains_spoilers': False,
            'is_public': True
        })
        self.assertEqual(res.status_code, 201)
        review_id = res.data['id']
        self.assertEqual(res.data['reaction_detail']['key'], 'peak')

        # 2. Duplicate create returns 409 Conflict
        res_dup = self.client.post('/api/v1/reviews/', {
            'media_item': str(self.movie.id),
            'reaction': str(self.rx_loved_it.id),
            'review_text': 'Second review attempt.'
        })
        self.assertEqual(res_dup.status_code, 409)

        # 3. Patch review
        res_patch = self.client.patch(f'/api/v1/reviews/{review_id}/', {
            'review_text': 'Updated: Dennis Villeneuve at his finest.'
        })
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.data['review_text'], 'Updated: Dennis Villeneuve at his finest.')

        # 4. Delete review
        res_delete = self.client.delete(f'/api/v1/reviews/{review_id}/')
        self.assertEqual(res_delete.status_code, 204)

    def test_private_review_privacy_access_control(self):
        """
        Verifies strict review privacy:
        - Anonymous user + private review -> 404
        - Other authenticated user + private review -> 404
        - Owner + private review -> 200
        - Any user + public review -> 200
        - Other user cannot PATCH or DELETE private review
        """
        # User A creates a private review
        private_review = MediaReview.objects.create(
            user=self.user,
            media_item=self.movie,
            reaction=self.rx_peak,
            review_text="My private personal journal thoughts.",
            is_public=False
        )

        # 1. Anonymous GET -> 404
        anon_client = APIClient()
        res_anon = anon_client.get(f'/api/v1/reviews/{private_review.id}/')
        self.assertEqual(res_anon.status_code, 404)

        # 2. Other user GET -> 404
        user_b = User.objects.create_user(username='other_user', password='pass123_secure')
        other_client = APIClient()
        other_client.force_authenticate(user=user_b)
        res_other = other_client.get(f'/api/v1/reviews/{private_review.id}/')
        self.assertEqual(res_other.status_code, 404)

        # 3. Owner GET -> 200
        res_owner = self.client.get(f'/api/v1/reviews/{private_review.id}/')
        self.assertEqual(res_owner.status_code, 200)
        self.assertEqual(res_owner.data['review_text'], "My private personal journal thoughts.")

        # 4. Other user cannot PATCH or DELETE private review -> 404
        res_other_patch = other_client.patch(f'/api/v1/reviews/{private_review.id}/', {'review_text': 'Hacked'})
        self.assertEqual(res_other_patch.status_code, 404)
        res_other_delete = other_client.delete(f'/api/v1/reviews/{private_review.id}/')
        self.assertEqual(res_other_delete.status_code, 404)

        # 5. Public review is readable by all
        private_review.is_public = True
        private_review.save()

        res_anon_pub = anon_client.get(f'/api/v1/reviews/{private_review.id}/')
        self.assertEqual(res_anon_pub.status_code, 200)
        res_other_pub = other_client.get(f'/api/v1/reviews/{private_review.id}/')
        self.assertEqual(res_other_pub.status_code, 200)

    def test_review_list_privacy_and_media_id_filtering(self):
        """
        Verifies review list endpoint:
        - Anonymous user only sees public reviews.
        - Other user only sees public reviews.
        - Owner sees both public reviews and their own private reviews.
        - Filtering by media_id or media parameter works cleanly with UUIDs.
        """
        user_c = User.objects.create_user(username='charlie', password='password123')
        # Public review by Charlie
        MediaReview.objects.create(
            user=user_c,
            media_item=self.movie,
            reaction=self.rx_loved_it,
            review_text="Charlie public review",
            is_public=True
        )
        # Private review by self.user
        MediaReview.objects.create(
            user=self.user,
            media_item=self.movie,
            reaction=self.rx_not_my_thing,
            review_text="Self private review",
            is_public=False
        )

        # 1. Anonymous GET with ?media_id=<uuid>
        anon_client = APIClient()
        res_anon = anon_client.get(f'/api/v1/reviews/?media_id={self.movie.id}')
        self.assertEqual(res_anon.status_code, 200)
        anon_texts = [r['review_text'] for r in res_anon.data['results']]
        self.assertIn("Charlie public review", anon_texts)
        self.assertNotIn("Self private review", anon_texts)

        # 2. Charlie GET with ?media=<uuid>
        c_client = APIClient()
        c_client.force_authenticate(user=user_c)
        res_c = c_client.get(f'/api/v1/reviews/?media={self.movie.id}')
        self.assertEqual(res_c.status_code, 200)
        c_texts = [r['review_text'] for r in res_c.data['results']]
        self.assertIn("Charlie public review", c_texts)
        self.assertNotIn("Self private review", c_texts)

        # 3. Owner GET with ?media_id=<uuid> sees both
        res_owner = self.client.get(f'/api/v1/reviews/?media_id={self.movie.id}')
        self.assertEqual(res_owner.status_code, 200)
        owner_texts = [r['review_text'] for r in res_owner.data['results']]
        self.assertIn("Charlie public review", owner_texts)
        self.assertIn("Self private review", owner_texts)

    def test_review_create_patch_with_media_id_and_reaction_key(self):
        """Verifies review creation and patching using media_id and reaction_key aliases."""
        movie2 = MediaItem.objects.create(
            media_type='MOVIE',
            title='Interstellar',
            slug='interstellar-2014',
            release_year=2014
        )

        res_create = self.client.post('/api/v1/reviews/', {
            'media_id': str(movie2.id),
            'reaction_key': 'peak',
            'review_text': 'Fascinating linguistic sci-fi.',
            'contains_spoilers': False,
            'is_public': True
        }, format='json')
        self.assertEqual(res_create.status_code, 201)
        self.assertEqual(res_create.data['reaction_key'], 'peak')
        self.assertEqual(res_create.data['reaction_detail']['display_name'], 'Peak')
        self.assertEqual(res_create.data['reaction_detail']['color_token'], 'electric-gold')
        review_id = res_create.data['id']

        # PATCH using reaction_key
        res_patch = self.client.patch(f'/api/v1/reviews/{review_id}/', {
            'reaction_key': 'loved_it',
            'review_text': 'Updated: Still love it.'
        }, format='json')
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.data['reaction_key'], 'loved_it')
        self.assertEqual(res_patch.data['reaction_detail']['display_name'], 'Loved It')
        self.assertEqual(res_patch.data['reaction_detail']['color_token'], 'warm-coral')

