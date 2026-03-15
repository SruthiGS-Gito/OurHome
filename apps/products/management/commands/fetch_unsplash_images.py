"""
Management command: fetch_unsplash_images
Fetches a unique Unsplash photo per product using the product name as query.

Free tier: 50 requests/hour. 85 products = will hit limit mid-run.
The command stops cleanly on 403 and reports how many were updated.
Re-run after an hour to fetch the remainder (already-updated products are skipped).

Usage:
    python manage.py fetch_unsplash_images
    python manage.py fetch_unsplash_images --skip-existing   (skip products that already have an Unsplash URL)
    python manage.py fetch_unsplash_images --dry-run
"""

import os
import time
import requests
from django.core.management.base import BaseCommand
from apps.products.models import Product, ProductImage

UNSPLASH_ACCESS_KEY = os.environ.get('UNSPLASH_ACCESS_KEY', '')


class Command(BaseCommand):
    help = 'Fetch a unique Unsplash photo per product using product name as search query'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be fetched without writing to DB',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip products that already have an Unsplash URL (resume after rate-limit)',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,
            help='Seconds to wait between API calls (default: 2.0)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        skip_existing = options['skip_existing']
        delay = options['delay']

        if not UNSPLASH_ACCESS_KEY:
            self.stderr.write('ERROR: UNSPLASH_ACCESS_KEY not set in environment / .env')
            return

        products = list(Product.objects.all().order_by('category', 'name'))
        total = len(products)
        updated = skipped_existing = skipped_no_results = errors = 0

        self.stdout.write(f'Processing {total} products at {delay}s intervals...\n')

        for i, product in enumerate(products, 1):
            prefix = f'[{i:02d}/{total}]'

            # Skip products that already have an Unsplash URL if requested
            if skip_existing:
                img = ProductImage.objects.filter(product=product).first()
                if img and img.image_url and 'unsplash.com' in img.image_url:
                    self.stdout.write(f'{prefix} SKIP (has Unsplash): {product.name}')
                    skipped_existing += 1
                    continue

            if dry_run:
                self.stdout.write(f'{prefix} DRY RUN: would search "{product.name}"')
                continue

            try:
                resp = requests.get(
                    'https://api.unsplash.com/search/photos',
                    params={
                        'query': product.name,
                        'per_page': 1,
                        'orientation': 'landscape',
                    },
                    headers={'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'},
                    timeout=10,
                )

                if resp.status_code == 200:
                    results = resp.json().get('results', [])
                    if results:
                        image_url = results[0]['urls']['regular']
                        rows = ProductImage.objects.filter(product=product)
                        if rows.exists():
                            rows.update(image_url=image_url)
                        else:
                            ProductImage.objects.create(
                                product=product,
                                image_url=image_url,
                                is_primary=True,
                                caption=product.brand,
                            )
                        updated += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'{prefix} OK: {product.name}')
                        )
                    else:
                        skipped_no_results += 1
                        self.stdout.write(
                            f'{prefix} NO RESULTS: {product.name}'
                        )

                elif resp.status_code == 403:
                    self.stdout.write(
                        self.style.WARNING(
                            f'\n{prefix} RATE LIMITED (403) — stopping early.\n'
                            f'Re-run with --skip-existing to resume from here.'
                        )
                    )
                    break

                else:
                    errors += 1
                    self.stderr.write(
                        f'{prefix} HTTP {resp.status_code}: {product.name} — {resp.text[:80]}'
                    )

            except Exception as e:
                errors += 1
                self.stderr.write(f'{prefix} ERROR: {product.name} — {e}')

            time.sleep(delay)

        self.stdout.write('\n' + '-' * 50)
        self.stdout.write(self.style.SUCCESS(f'Updated:          {updated}'))
        if skipped_existing:
            self.stdout.write(f'Skipped (had URL): {skipped_existing}')
        if skipped_no_results:
            self.stdout.write(f'No results:        {skipped_no_results}')
        if errors:
            self.stdout.write(self.style.ERROR(f'Errors:            {errors}'))
        self.stdout.write(f'Remaining:         {total - updated - skipped_existing - skipped_no_results - errors}')
