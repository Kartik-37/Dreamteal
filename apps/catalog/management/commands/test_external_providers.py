"""
Optional management command to test live reachability of external metadata providers:
- TMDB (if TMDB_ACCESS_TOKEN or TMDB_API_KEY is configured)
- AniList (public GraphQL)
- Jikan (public REST)
- RAWG (if RAWG_API_KEY is configured)

Usage:
    python manage.py test_external_providers
"""

import sys
from django.conf import settings
from django.core.management.base import BaseCommand
from apps.catalog.providers.anilist import AniListProvider
from apps.catalog.providers.jikan import JikanProvider
from apps.catalog.providers.rawg import RAWGProvider
from apps.catalog.providers.tmdb import TMDBProvider


class Command(BaseCommand):
    help = "Tests connectivity and normalization with external metadata providers."

    def handle(self, *args, **options):
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')

        self.stdout.write(self.style.MIGRATE_HEADING("Testing External Metadata Providers..."))

        # 1. AniList (Public GraphQL)
        self.stdout.write("\n[1/4] Testing AniList Provider (Public GraphQL)...")
        anilist = AniListProvider()
        try:
            manga_results = anilist.search("Chainsaw Man", limit=2)
            if manga_results:
                r = manga_results[0]
                self.stdout.write(self.style.SUCCESS(f"  OK: Found '{r.title}' (ID: {r.external_id}, Year: {r.release_year})"))
            else:
                self.stdout.write(self.style.WARNING("  Warning: No results returned."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Failed: {e}"))

        # 2. Jikan (Public REST)
        self.stdout.write("\n[2/4] Testing Jikan Provider (Public REST Fallback)...")
        jikan = JikanProvider()
        try:
            jikan_results = jikan.search("Monster", limit=2)
            if jikan_results:
                r = jikan_results[0]
                self.stdout.write(self.style.SUCCESS(f"  OK: Found '{r.title}' (ID: {r.external_id}, Year: {r.release_year})"))
            else:
                self.stdout.write(self.style.WARNING("  Warning: No results returned."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Failed: {e}"))

        # 3. TMDB (Requires Access Token or API Key)
        self.stdout.write("\n[3/4] Testing TMDB Provider...")
        tmdb = TMDBProvider()
        if tmdb.access_token or tmdb.api_key:
            try:
                tmdb_results = tmdb.search("Inception", limit=2, media_type='MOVIE')
                if tmdb_results:
                    r = tmdb_results[0]
                    self.stdout.write(self.style.SUCCESS(f"  OK: Found '{r.title}' (ID: {r.external_id}, Year: {r.release_year})"))
                else:
                    self.stdout.write(self.style.WARNING("  Warning: No results returned."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Failed: {e}"))
        else:
            self.stdout.write(self.style.NOTICE("  Skipped: TMDB_ACCESS_TOKEN or TMDB_API_KEY not configured in environment."))

        # 4. RAWG (Requires RAWG_API_KEY)
        self.stdout.write("\n[4/4] Testing RAWG Provider...")
        rawg = RAWGProvider()
        if rawg.api_key:
            try:
                rawg_results = rawg.search("Portal 2", limit=2)
                if rawg_results:
                    r = rawg_results[0]
                    self.stdout.write(self.style.SUCCESS(f"  OK: Found '{r.title}' (ID: {r.external_id}, Year: {r.release_year})"))
                else:
                    self.stdout.write(self.style.WARNING("  Warning: No results returned."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Failed: {e}"))
        else:
            self.stdout.write(self.style.NOTICE("  Skipped: RAWG_API_KEY not configured in environment."))

        self.stdout.write(self.style.SUCCESS("\nProvider Connectivity Check Complete!"))
