"""
management/commands/estimate_remaining_prices.py

For products not matched by apply_pwd_sor_prices (still price_source='seed_baseline'),
uses Claude AI to estimate Kerala market prices based on PWD SOR 2024 knowledge.

Run AFTER apply_pwd_sor_prices:
    python manage.py apply_pwd_sor_prices
    python manage.py estimate_remaining_prices

Usage:
    python manage.py estimate_remaining_prices
    python manage.py estimate_remaining_prices --dry-run    # list which products would be estimated
    python manage.py estimate_remaining_prices --limit 5    # process only N products (for testing)
"""

import json
import time
from decimal import Decimal, InvalidOperation

import anthropic
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.products.models import Product

PROMPT_TEMPLATE = """You are a construction material price expert for Kerala, India.
Based on Kerala PWD Schedule of Rates 2024 and current market knowledge,
provide price estimates for this material.

Material: {name}
Brand: {brand}
Category: {category}
Unit: {unit}
Description: {description}

Return ONLY valid JSON, no explanation, no markdown:
{{
    "market_price": <number>,
    "mrp": <number>,
    "confidence": "high" | "medium" | "low",
    "reasoning": "<one sentence>"
}}

Rules:
- Base prices on Kerala market rates in INR
- mrp must always be >= market_price
- If genuinely uncertain, set confidence to "low"
- Never fabricate — if you cannot estimate reliably, return confidence: "low" with your best guess
- Prices should be per {unit} as specified"""


class Command(BaseCommand):
    help = 'Use Claude AI to estimate prices for products not covered by PWD SOR.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List products that would be estimated without calling the API.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Process only N products (useful for testing).',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']

        # Only process products still on seed_baseline (not yet priced from SOR)
        qs = Product.objects.filter(is_active=True, price_source='seed_baseline').order_by('category', 'name')
        if limit:
            qs = qs[:limit]

        products = list(qs)

        if not products:
            self.stdout.write(self.style.SUCCESS('No seed_baseline products remaining — nothing to estimate.'))
            return

        self.stdout.write(f'Found {len(products)} product(s) to estimate.\n')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no API calls will be made:\n'))
            for p in products:
                self.stdout.write(f'  • {p.name} ({p.category}, {p.unit})')
            return

        if not settings.ANTHROPIC_API_KEY:
            self.stderr.write(self.style.ERROR(
                'ANTHROPIC_API_KEY is not set. Add it to your .env file.'
            ))
            return

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        now = timezone.now()

        counts = {'high': 0, 'medium': 0, 'low': 0, 'error': 0}

        for i, product in enumerate(products, 1):
            self.stdout.write(f'[{i}/{len(products)}] Estimating: {product.name} ...')

            prompt = PROMPT_TEMPLATE.format(
                name=product.name,
                brand=product.brand,
                category=product.get_category_display(),
                unit=product.unit,
                description=(product.description[:200] if product.description else ''),
            )

            try:
                response = client.messages.create(
                    model='claude-haiku-4-5-20251001',
                    max_tokens=200,
                    messages=[{'role': 'user', 'content': prompt}],
                )

                raw = response.content[0].text.strip()

                # Strip markdown code fences if model wraps in ```json ... ```
                if raw.startswith('```'):
                    raw = raw.split('```')[1]
                    if raw.startswith('json'):
                        raw = raw[4:]
                    raw = raw.strip()

                parsed = json.loads(raw)

                market_price = Decimal(str(parsed['market_price']))
                mrp = Decimal(str(parsed['mrp']))
                confidence = parsed.get('confidence', 'low')
                reasoning = parsed.get('reasoning', '')[:190]

                # Sanity checks
                if market_price <= 0 or mrp < market_price:
                    raise ValueError(f'Invalid prices: market={market_price}, mrp={mrp}')
                if confidence not in ('high', 'medium', 'low'):
                    confidence = 'low'

                product.price = market_price
                product.mrp = mrp
                product.price_source = 'ai_estimate'
                product.price_confidence = confidence
                product.price_source_reference = f'AI estimate: {reasoning}'
                product.price_updated_at = now
                product.save(update_fields=[
                    'price', 'mrp', 'price_source', 'price_confidence',
                    'price_source_reference', 'price_updated_at',
                ])

                counts[confidence] += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  OK  Rs.{market_price} ({confidence} confidence)'
                    )
                )

            except (json.JSONDecodeError, KeyError, ValueError, InvalidOperation) as exc:
                counts['error'] += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Parse error: {exc}')
                )
            except anthropic.APIError as exc:
                counts['error'] += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ API error: {exc}')
                )

            # Rate-limit courtesy delay
            if i < len(products):
                time.sleep(0.5)

        # ── Final summary ─────────────────────────────────────────────────
        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(self.style.SUCCESS('ESTIMATE SUMMARY'))
        self.stdout.write(f'  High confidence  : {counts["high"]}')
        self.stdout.write(f'  Medium confidence: {counts["medium"]}')
        self.stdout.write(f'  Low confidence   : {counts["low"]}')
        if counts['error']:
            self.stdout.write(self.style.ERROR(f'  Errors (skipped) : {counts["error"]}'))
        total_ok = counts['high'] + counts['medium'] + counts['low']
        self.stdout.write(f'\n  {total_ok} products updated, {counts["error"]} failed.')
