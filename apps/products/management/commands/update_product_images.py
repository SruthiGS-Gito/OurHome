"""
management/commands/update_product_images.py

Maps every product to a category-correct static image from
static/images/products/.

Available static images:
    cement.jpg  steel.jpg  brick.jpg  aac.jpg  sand.jpg
    aggregate.jpg  tile.jpg  paint.jpg  waterproofing.jpg

Rule:
  - category → /static/images/products/{category}.jpg
  - Exception: Siporex AAC Blocks → aac.jpg  (dedicated photo)
  - 'sand' and 'aggregate' are separate static files

Usage:
    python manage.py update_product_images          # skip products already set
    python manage.py update_product_images --force  # replace all images
"""

from django.core.management.base import BaseCommand
from apps.products.models import Product, ProductImage

# Maps product category code → static image path
CATEGORY_IMAGE = {
    'cement':        '/static/images/products/cement.jpg',
    'steel':         '/static/images/products/steel.jpg',
    'brick':         '/static/images/products/brick.jpg',
    'sand':          '/static/images/products/sand.jpg',
    'aggregate':     '/static/images/products/aggregate.jpg',
    'tile':          '/static/images/products/tile.jpg',
    'paint':         '/static/images/products/paint.jpg',
    'waterproofing': '/static/images/products/waterproofing.jpg',
}

# Per-slug overrides (take priority over the category mapping above)
SLUG_OVERRIDES = {
    'siporex-aac-blocks-600200200mm': '/static/images/products/aac.jpg',
}

FALLBACK = '/static/images/products/cement.jpg'


def _image_for(product):
    if product.slug in SLUG_OVERRIDES:
        return SLUG_OVERRIDES[product.slug]
    return CATEGORY_IMAGE.get(product.category, FALLBACK)


class Command(BaseCommand):
    help = 'Assign category-correct static images to every product.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Replace existing ProductImage records (default: skip products that already have images).',
        )

    def handle(self, *args, **options):
        force   = options['force']
        updated = 0
        skipped = 0

        for product in Product.objects.all().order_by('category', 'name'):
            url      = _image_for(product)
            existing = product.images.filter(is_primary=True).first()

            if existing and not force:
                self.stdout.write(f'  SKIP  {product.name[:60]}')
                skipped += 1
                continue

            if existing:
                existing.image_url = url
                existing.caption   = product.name
                existing.save(update_fields=['image_url', 'caption'])
            else:
                ProductImage.objects.create(
                    product=product,
                    image_url=url,
                    caption=product.name,
                    is_primary=True,
                    sort_order=0,
                )

            label = url.split('/')[-1]
            self.stdout.write(self.style.SUCCESS(f'  SET   {product.name[:55]:55s}  {label}'))
            updated += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Done. {updated} updated, {skipped} skipped.'))
