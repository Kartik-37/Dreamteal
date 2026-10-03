"""
Django management command to seed DreamTeal database with initial foundations:
1. Five Approved Reaction Definitions (Peak, Loved It, Good Time, Not My Thing, Skip)
2. Standard test development user
3. Standard Genres & Thematic Vibe Tags
4. Sample multi-category media items with category extensions (Movie, Series, Manga, Game)
5. Sample tracking statuses, progress models, diary logs, and qualitative reviews
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.catalog.models import (
    Genre, Tag, MediaItem, MovieDetail, SeriesDetail, MangaDetail, GameDetail
)
from apps.tracking.models import (
    UserMediaStatus, UserMediaProgress, SeriesProgress, MangaProgress, GameProgress, DiaryLog
)
from apps.reviews.models import ReactionDefinition, MediaReview

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds initial DreamTeal reaction definitions, catalog items, and development test data."

    def handle(self, *args, **options):
        import sys
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')

        self.stdout.write(self.style.MIGRATE_HEADING("Starting DreamTeal Database Seed..."))

        # ---------------------------------------------------------
        # 1. Five Approved Reaction Definitions (Strictly Qualitative)
        # ---------------------------------------------------------
        reactions_data = [
            {
                'key': 'peak',
                'display_name': 'Peak',
                'description': 'An exceptional experience that the user strongly recommends.',
                'sort_order': 1,
            },
            {
                'key': 'loved_it',
                'display_name': 'Loved It',
                'description': 'A genuinely enjoyable experience that the user highly values.',
                'sort_order': 2,
            },
            {
                'key': 'good_time',
                'display_name': 'Good Time',
                'description': 'Enjoyable and worth experiencing, but not exceptional.',
                'sort_order': 3,
            },
            {
                'key': 'not_my_thing',
                'display_name': 'Not My Thing',
                'description': 'The user did not connect with it, even if the media may have strengths.',
                'sort_order': 4,
            },
            {
                'key': 'skip',
                'display_name': 'Skip',
                'description': 'The user would not recommend spending time on it.',
                'sort_order': 5,
            },
        ]

        created_reactions = {}
        for r_data in reactions_data:
            reaction, created = ReactionDefinition.objects.update_or_create(
                key=r_data['key'],
                defaults=r_data
            )
            created_reactions[r_data['key']] = reaction
            status_text = "Created" if created else "Updated"
            self.stdout.write(f"  [{status_text}] Reaction: {reaction.display_name}")

        # ---------------------------------------------------------
        # 1b. External Providers (TMDB, AniList, Jikan, RAWG)
        # ---------------------------------------------------------
        from apps.catalog.models import ExternalProvider, ExternalMediaMapping

        providers_data = [
            {
                'provider_key': 'tmdb',
                'display_name': 'TMDB',
                'base_url': 'https://www.themoviedb.org',
                'attribution_text': 'This product uses the TMDB API but is not endorsed or certified by TMDB.',
                'attribution_url': 'https://www.themoviedb.org',
                'active': True,
            },
            {
                'provider_key': 'anilist',
                'display_name': 'AniList',
                'base_url': 'https://anilist.co',
                'attribution_text': 'Manga and manhwa metadata powered by the AniList GraphQL API.',
                'attribution_url': 'https://anilist.co',
                'active': True,
            },
            {
                'provider_key': 'jikan',
                'display_name': 'Jikan (MyAnimeList)',
                'base_url': 'https://jikan.moe',
                'attribution_text': 'Fallback manga metadata provided by Jikan, an open-source API for MyAnimeList.',
                'attribution_url': 'https://jikan.moe',
                'active': True,
            },
            {
                'provider_key': 'rawg',
                'display_name': 'RAWG',
                'base_url': 'https://rawg.io',
                'attribution_text': 'Video game data and metadata provided by RAWG.io.',
                'attribution_url': 'https://rawg.io',
                'active': True,
            },
        ]
        created_providers = {}
        for p_data in providers_data:
            provider, p_created = ExternalProvider.objects.update_or_create(
                provider_key=p_data['provider_key'],
                defaults=p_data
            )
            created_providers[p_data['provider_key']] = provider
            p_status = "Created" if p_created else "Updated"
            self.stdout.write(f"  [{p_status}] External Provider: {provider.display_name}")

        # ---------------------------------------------------------
        # 2. Standard Development Test User
        # ---------------------------------------------------------
        test_user, user_created = User.objects.get_or_create(
            username='dreamteal_tester',
            defaults={
                'email': 'tester@dreamteal.local',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if user_created:
            test_user.set_password('dreamteal_pass123')
            test_user.save()
            self.stdout.write(self.style.SUCCESS(f"  [Created] Test User: {test_user.username}"))
        else:
            self.stdout.write(f"  [Found] Test User: {test_user.username}")

        # Ensure user profile exists
        if hasattr(test_user, 'profile'):
            test_user.profile.display_name = "DreamTeal Explorer"
            test_user.profile.bio = "Tracking and reviewing across movies, shows, manhwa, and games."
            test_user.profile.save()

        # ---------------------------------------------------------
        # 3. Standard Genres & Thematic Vibe Tags
        # ---------------------------------------------------------
        genres = [
            ('Action', 'action'),
            ('Sci-Fi', 'sci-fi'),
            ('Crime', 'crime'),
            ('Mystery', 'mystery'),
            ('Drama', 'drama'),
            ('Fantasy', 'fantasy'),
            ('Cyberpunk', 'cyberpunk'),
            ('Comedy', 'comedy'),
            ('RPG', 'rpg'),
            ('Psychological', 'psychological'),
        ]
        genre_objs = {}
        for name, slug in genres:
            g, _ = Genre.objects.get_or_create(name=name, defaults={'slug': slug})
            genre_objs[slug] = g

        tags = [
            ('Mind-Bending', 'mind-bending'),
            ('Dark Fantasy', 'dark-fantasy'),
            ('Neo-Noir', 'neo-noir'),
            ('Detective', 'detective'),
            ('Cozy', 'cozy'),
            ('Fast-Paced', 'fast-paced'),
            ('Open World', 'open-world'),
            ('Dystopian', 'dystopian'),
        ]
        tag_objs = {}
        for name, slug in tags:
            t, _ = Tag.objects.get_or_create(name=name, defaults={'slug': slug})
            tag_objs[slug] = t

        self.stdout.write(f"  [Created] {len(genre_objs)} Genres & {len(tag_objs)} Tags.")

        # ---------------------------------------------------------
        # 4. Multi-Category Media Catalog Items
        # ---------------------------------------------------------

        # A. Movie: The Batman
        batman, _ = MediaItem.objects.get_or_create(
            slug='the-batman-2022',
            defaults={
                'title': 'The Batman',
                'media_type': MediaItem.MediaType.MOVIE,
                'release_year': 2022,
                'synopsis': 'When a sadistic serial killer begins murdering key political figures in Gotham, Batman is forced to investigate the city\'s hidden corruption.',
                'poster_url': 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500',
            }
        )
        batman.genres.set([genre_objs['action'], genre_objs['crime'], genre_objs['mystery']])
        batman.tags.set([tag_objs['neo-noir'], tag_objs['detective']])
        MovieDetail.objects.update_or_create(
            media_item=batman,
            defaults={
                'director': 'Matt Reeves',
                'runtime_minutes': 176,
                'studio': 'Warner Bros. Pictures',
                'ott_providers': ['Max', 'Prime Video'],
            }
        )

        # B. TV Series: Severance
        severance, _ = MediaItem.objects.get_or_create(
            slug='severance-2022',
            defaults={
                'title': 'Severance',
                'media_type': MediaItem.MediaType.SERIES,
                'release_year': 2022,
                'synopsis': 'Mark leads a team of office workers whose memories have been surgically divided between their work and personal lives.',
                'poster_url': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=500',
            }
        )
        severance.genres.set([genre_objs['sci-fi'], genre_objs['drama'], genre_objs['mystery'], genre_objs['psychological']])
        severance.tags.set([tag_objs['mind-bending'], tag_objs['dystopian']])
        SeriesDetail.objects.update_or_create(
            media_item=severance,
            defaults={
                'creators': 'Dan Erickson',
                'total_seasons': 2,
                'total_episodes': 19,
                'status': SeriesDetail.SeriesStatus.AIRING,
                'ott_providers': ['Apple TV+'],
            }
        )

        # C. Manga / Manhwa: Solo Leveling
        solo_leveling, _ = MediaItem.objects.get_or_create(
            slug='solo-leveling-2018',
            defaults={
                'title': 'Solo Leveling',
                'media_type': MediaItem.MediaType.MANGA,
                'release_year': 2018,
                'synopsis': 'In a world where hunters must battle deadly monsters, weak hunter Sung Jin-woo awakens as the only human capable of leveling up.',
                'poster_url': 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=500',
            }
        )
        solo_leveling.genres.set([genre_objs['action'], genre_objs['fantasy']])
        solo_leveling.tags.set([tag_objs['dark-fantasy'], tag_objs['fast-paced']])
        MangaDetail.objects.update_or_create(
            media_item=solo_leveling,
            defaults={
                'author': 'Chugong',
                'artist': 'DUBU (REDICE STUDIO)',
                'manga_type': MangaDetail.MangaType.MANHWA,
                'status': MangaDetail.PublicationStatus.FINISHED,
                'total_chapters': 200,
            }
        )

        # D. Video Game: Cyberpunk 2077
        cyberpunk, _ = MediaItem.objects.get_or_create(
            slug='cyberpunk-2077-2020',
            defaults={
                'title': 'Cyberpunk 2077',
                'media_type': MediaItem.MediaType.GAME,
                'release_year': 2020,
                'synopsis': 'An open-world, action-adventure RPG set in Night City, a megalopolis obsessed with power, glamour and body modification.',
                'poster_url': 'https://images.unsplash.com/photo-1542751371-adc38448a05e?w=500',
            }
        )
        cyberpunk.genres.set([genre_objs['action'], genre_objs['rpg'], genre_objs['cyberpunk'], genre_objs['sci-fi']])
        cyberpunk.tags.set([tag_objs['open-world'], tag_objs['dystopian']])
        GameDetail.objects.update_or_create(
            media_item=cyberpunk,
            defaults={
                'developer': 'CD Projekt Red',
                'publisher': 'CD Projekt',
                'platforms': ['PC', 'PS5', 'Xbox Series X'],
                'average_story_hours': Decimal('30.0'),
            }
        )

        self.stdout.write(self.style.SUCCESS("  [Created] 4 Multi-Category Media Items with Details."))

        # ---------------------------------------------------------
        # 5. User Tracking, Progress, Diary Logs, and Reviews
        # ---------------------------------------------------------

        # Statuses
        UserMediaStatus.objects.update_or_create(
            user=test_user,
            media_item=batman,
            defaults={'status': UserMediaStatus.StatusChoices.WATCHED, 'is_favorite': True}
        )
        UserMediaStatus.objects.update_or_create(
            user=test_user,
            media_item=severance,
            defaults={'status': UserMediaStatus.StatusChoices.WATCHING, 'is_favorite': True}
        )
        UserMediaStatus.objects.update_or_create(
            user=test_user,
            media_item=solo_leveling,
            defaults={'status': UserMediaStatus.StatusChoices.READING, 'is_favorite': False}
        )
        UserMediaStatus.objects.update_or_create(
            user=test_user,
            media_item=cyberpunk,
            defaults={'status': UserMediaStatus.StatusChoices.PLAYING, 'is_favorite': True}
        )

        # Progress Models
        # Severance (SeriesProgress)
        prog_sev, _ = UserMediaProgress.objects.get_or_create(user=test_user, media_item=severance)
        SeriesProgress.objects.update_or_create(
            progress=prog_sev,
            defaults={'current_season': 1, 'current_episode': 9, 'last_watched_episode_title': 'The We We Are'}
        )

        # Solo Leveling (MangaProgress)
        prog_solo, _ = UserMediaProgress.objects.get_or_create(user=test_user, media_item=solo_leveling)
        MangaProgress.objects.update_or_create(
            progress=prog_solo,
            defaults={'current_chapter': 120, 'current_volume': 9}
        )

        # Cyberpunk (GameProgress)
        prog_cp, _ = UserMediaProgress.objects.get_or_create(user=test_user, media_item=cyberpunk)
        GameProgress.objects.update_or_create(
            progress=prog_cp,
            defaults={'hours_played': Decimal('45.5'), 'completion_type': GameProgress.CompletionType.MAIN_STORY, 'platform_played_on': 'PC'}
        )

        # Sample ExternalMediaMappings for demo media items
        ExternalMediaMapping.objects.update_or_create(
            provider=created_providers['tmdb'],
            external_id='414906',
            defaults={
                'media_item': batman,
                'external_url': 'https://www.themoviedb.org/movie/414906-the-batman',
            }
        )
        ExternalMediaMapping.objects.update_or_create(
            provider=created_providers['tmdb'],
            external_id='97546',
            defaults={
                'media_item': severance,
                'external_url': 'https://www.themoviedb.org/tv/97546-severance',
            }
        )
        ExternalMediaMapping.objects.update_or_create(
            provider=created_providers['anilist'],
            external_id='105398',
            defaults={
                'media_item': solo_leveling,
                'external_url': 'https://anilist.co/manga/105398/Solo-Leveling/',
            }
        )
        ExternalMediaMapping.objects.update_or_create(
            provider=created_providers['rawg'],
            external_id='3328',
            defaults={
                'media_item': cyberpunk,
                'external_url': 'https://rawg.io/games/the-witcher-3-wild-hunt',
            }
        )

        # History-Preserving Diary Logs (Demonstrating initial log + rewatch)
        if not DiaryLog.objects.filter(user=test_user, media_item=batman, is_rewatch_or_replay=False).exists():
            DiaryLog.objects.create(
                user=test_user,
                media_item=batman,
                logged_date=timezone.now().date(),
                is_rewatch_or_replay=False,
                session_notes='Incredible theater premiere. The score and cinematography set a new standard.',
                progress_snapshot={'watch_format': 'IMAX'}
            )
        if not DiaryLog.objects.filter(user=test_user, media_item=batman, is_rewatch_or_replay=True).exists():
            DiaryLog.objects.create(
                user=test_user,
                media_item=batman,
                logged_date=timezone.now().date(),
                is_rewatch_or_replay=True,
                session_notes='Rewatched at home on 4K Blu-ray. The investigation scenes hold up brilliantly.',
                progress_snapshot={'watch_format': '4K Home Cinema'}
            )

        # Qualitative Review using approved 'peak' reaction
        MediaReview.objects.update_or_create(
            user=test_user,
            media_item=severance,
            defaults={
                'reaction': created_reactions['peak'],
                'review_text': 'One of the smartest psychological thrillers ever created for television. Flawless pacing and concept execution.',
                'contains_spoilers': False,
                'is_public': True
            }
        )

        self.stdout.write(self.style.SUCCESS("  [Created] Sample tracking statuses, progress extensions, diary logs, review, and provider mappings."))
        self.stdout.write(self.style.SUCCESS("DreamTeal Database Seed Completed Successfully!"))
