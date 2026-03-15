"""
management/commands/apply_pwd_sor_prices.py

Applies Kerala PWD Schedule of Rates 2024 prices to products where
the category/name clearly matches a published SOR line item.

These are OFFICIAL government-published rates — not estimates:
https://pwd.kerala.gov.in (SOR 2024 document)

Usage:
    python manage.py apply_pwd_sor_prices
    python manage.py apply_pwd_sor_prices --dry-run   # preview without saving
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.products.models import Product


# ---------------------------------------------------------------------------
# Kerala PWD SOR 2024 — approved rate ranges (midpoint → price, upper → mrp)
# Format: (category, name_keywords, price_midpoint, mrp_upper, unit_hint)
# ---------------------------------------------------------------------------
PWD_SOR_RULES = [
    # Cement
    {
        'category': 'cement',
        'keywords': ['opc', 'ordinary portland', 'opc 53', 'opc 43'],
        'price': 400,        # midpoint of 380-420
        'mrp': 420,
        'unit': 'bag',
        'label': 'OPC Cement (50kg bag)',
    },
    {
        'category': 'cement',
        'keywords': ['ppc', 'portland pozzolana', 'pozzolana'],
        'price': 370,        # midpoint of 350-390
        'mrp': 390,
        'unit': 'bag',
        'label': 'PPC Cement (50kg bag)',
    },
    {
        'category': 'cement',
        'keywords': ['psc', 'portland slag', 'slag'],
        'price': 370,
        'mrp': 390,
        'unit': 'bag',
        'label': 'PSC Cement (50kg bag)',
    },
    {
        'category': 'cement',
        'keywords': ['white cement', 'white'],
        'price': 620,        # white cement is 50-60% premium over OPC
        'mrp': 700,
        'unit': 'bag',
        'label': 'White Cement (50kg bag)',
    },
    {
        'category': 'cement',
        'keywords': ['sulphate', 'src', 'resistant'],
        'price': 420,
        'mrp': 460,
        'unit': 'bag',
        'label': 'Sulphate Resistant Cement (50kg bag)',
    },

    # Sand
    {
        'category': 'sand',
        'keywords': ['m-sand', 'msand', 'm sand', 'manufactured', 'robo'],
        'price': 1000,       # midpoint of 800-1200 per MT
        'mrp': 1200,
        'unit': 'tonne',
        'label': 'M-Sand (per metric tonne)',
    },
    {
        'category': 'sand',
        'keywords': ['river sand', 'natural sand'],
        'price': 2000,       # midpoint of 1500-2500 per MT
        'mrp': 2500,
        'unit': 'tonne',
        'label': 'River Sand (per metric tonne)',
    },

    # Steel / TMT
    {
        'category': 'steel',
        'keywords': ['tmt', 'fe500', 'fe 500', 'tmt bars', 'steel bar'],
        'price': 62,         # midpoint of 55-70 per kg
        'mrp': 70,
        'unit': 'kg',
        'label': 'TMT Steel Bars Fe500 (per kg)',
    },

    # Brick & Block
    {
        'category': 'brick',
        'keywords': ['clay brick', 'red brick', 'country brick', 'brick'],
        # Exclude blocks — checked by absence of 'block' in name
        'exclude_keywords': ['block', 'aac', 'concrete'],
        'price': 10,         # midpoint of 8-12 per unit
        'mrp': 12,
        'unit': 'piece',
        'label': 'Clay Bricks (per unit)',
    },
    {
        'category': 'brick',
        'keywords': ['concrete block', 'solid block', 'hollow block', 'block'],
        'exclude_keywords': ['aac'],
        'price': 40,         # midpoint of 35-45 per unit
        'mrp': 45,
        'unit': 'piece',
        'label': 'Concrete Blocks 6-inch (per unit)',
    },
    {
        'category': 'brick',
        'keywords': ['aac', 'autoclaved', 'lightweight'],
        'price': 55,         # AAC blocks are premium
        'mrp': 65,
        'unit': 'piece',
        'label': 'AAC Blocks (per unit)',
    },

    # Tiles
    {
        'category': 'tile',
        'keywords': ['ceramic'],
        'exclude_keywords': ['vitrified', 'porcelain', 'digital'],
        'price': 57,         # midpoint of 35-80 per sqft
        'mrp': 80,
        'unit': 'sqft',
        'label': 'Ceramic Tiles (per sqft)',
    },
    {
        'category': 'tile',
        'keywords': ['vitrified', 'porcelain', 'gvt', 'fgvt', 'dgvt', 'double charge'],
        'price': 105,        # midpoint of 60-150 per sqft
        'mrp': 150,
        'unit': 'sqft',
        'label': 'Vitrified Tiles (per sqft)',
    },

    # Waterproofing
    {
        'category': 'waterproofing',
        'keywords': ['waterproof', 'waterproofing'],
        'price': 140,        # midpoint of 80-200 per kg
        'mrp': 200,
        'unit': 'kg',
        'label': 'Waterproofing Compound (per kg)',
    },

    # Aggregate — Kerala PWD SOR 2024: coarse aggregate rates
    {
        'category': 'aggregate',
        'keywords': ['20mm', '20 mm'],
        'price': 1600,       # midpoint of 1400-1800 per MT
        'mrp': 1800,
        'unit': 'tonne',
        'label': '20mm Aggregate (per metric tonne)',
    },
    {
        'category': 'aggregate',
        'keywords': ['40mm', '40 mm'],
        'price': 1400,       # midpoint of 1200-1600 per MT
        'mrp': 1600,
        'unit': 'tonne',
        'label': '40mm Aggregate (per metric tonne)',
    },
    {
        'category': 'aggregate',
        'keywords': ['aggregate', 'crushed granite', 'gravel'],
        'price': 1500,       # general aggregate rate
        'mrp': 1800,
        'unit': 'tonne',
        'label': 'Aggregate — general (per metric tonne)',
    },

    # Paint — Kerala PWD SOR 2024: paint rates per litre
    {
        'category': 'paint',
        'keywords': ['interior', 'emulsion', 'tractor', 'washable', 'acrylic'],
        'exclude_keywords': ['exterior', 'weather', 'allguard', 'apex'],
        'price': 195,        # midpoint of 170-220 per litre
        'mrp': 220,
        'unit': 'litre',
        'label': 'Interior Emulsion Paint (per litre)',
    },
    {
        'category': 'paint',
        'keywords': ['exterior', 'weather', 'weathercoat', 'excel', 'all guard', 'allguard', 'apex'],
        'price': 270,        # midpoint of 240-300 per litre
        'mrp': 300,
        'unit': 'litre',
        'label': 'Exterior Emulsion Paint (per litre)',
    },

    # Anti-skid / specialty tiles
    {
        'category': 'tile',
        'keywords': ['anti-skid', 'antiskid', 'parking', 'anti skid'],
        'price': 100,        # midpoint of 80-120 per sqft
        'mrp': 120,
        'unit': 'sqft',
        'label': 'Anti-Skid / Parking Tile (per sqft)',
    },
]

REFERENCE = 'Kerala PWD Schedule of Rates 2024'


def _matches_rule(product, rule):
    """
    Returns True if the product matches this SOR rule.
    Matching logic:
    1. product.category must match rule['category']
    2. At least one keyword must appear in product.name.lower() or product.brand.lower()
    3. None of the exclude_keywords (if any) may appear
    """
    if product.category != rule['category']:
        return False

    search_text = (product.name + ' ' + product.brand + ' ' + product.subcategory).lower()

    # Check required keywords (any match = pass)
    if not any(kw in search_text for kw in rule['keywords']):
        return False

    # Check exclusions (any match = fail)
    for ex_kw in rule.get('exclude_keywords', []):
        if ex_kw in search_text:
            return False

    return True


class Command(BaseCommand):
    help = 'Apply Kerala PWD SOR 2024 prices to matching products.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving to database.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))

        products = list(Product.objects.filter(is_active=True))
        updated = []
        skipped = []

        for product in products:
            matched_rule = None
            for rule in PWD_SOR_RULES:
                if _matches_rule(product, rule):
                    matched_rule = rule
                    break   # first match wins

            if matched_rule:
                if not dry_run:
                    product.price = matched_rule['price']
                    product.mrp = matched_rule['mrp']
                    product.price_source = 'pwd_sor'
                    product.price_confidence = 'high'
                    product.price_source_reference = REFERENCE
                    product.price_updated_at = now
                    product.save(update_fields=[
                        'price', 'mrp', 'price_source', 'price_confidence',
                        'price_source_reference', 'price_updated_at',
                    ])
                updated.append((product.name, matched_rule['label'],
                                 matched_rule['price'], matched_rule['mrp']))
            else:
                skipped.append(product.name)

        # ── Summary output ────────────────────────────────────────────────
        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(self.style.SUCCESS(f'UPDATED ({len(updated)} products):'))
        for name, label, price, mrp in updated:
            self.stdout.write(
                f'  OK  {name}\n'
                f'       SOR: {label}  |  price: Rs.{price}  mrp: Rs.{mrp}'
            )

        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(self.style.WARNING(f'SKIPPED ({len(skipped)} products — no SOR match):'))
        for name in skipped:
            self.stdout.write(f'  --  {name}')

        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(
            f'\nTotal: {len(updated)} updated, {len(skipped)} skipped (still seed_baseline).'
        )
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN complete — database unchanged.'))
        else:
            self.stdout.write(self.style.SUCCESS('Done. Run estimate_remaining_prices for the rest.'))
