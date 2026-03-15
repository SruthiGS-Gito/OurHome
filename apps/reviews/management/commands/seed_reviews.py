"""
management/commands/seed_reviews.py

Seeds 10 realistic reviews for demo purposes.
All reviews are set is_approved=True so signals fire on creation and
product.average_rating / total_reviews / rating_breakdown are updated live.

DEMO-CRITICAL reviews:
  OPC 53  — Review 1: contractor WARNS about coastal use (reinforces the WARNING banner)
           — Review 2: engineer PRAISES inland / hot-dry performance
  PPC     — Review 3: homeowner PRAISES coastal Kerala (reinforces the SUITABLE banner)
           — Review 4: contractor PRAISES coastal Kochi performance

Usage:
    python manage.py seed_reviews          # add, skip existing
    python manage.py seed_reviews --clear  # wipe all reviews first
"""

from django.core.management.base import BaseCommand

from apps.products.models import Product
from apps.reviews.models import Review

REVIEWS = [

    # ─────────────────────────────────────────────────────────
    # UltraTech OPC 53 Grade Cement — 2 reviews
    # These make the climate WARNING pop in the demo.
    # ─────────────────────────────────────────────────────────
    {
        'product_name_contains': 'OPC 53',
        'rating': 2,
        'title': 'Avoid for coastal construction — learned the hard way',
        'review_text': (
            'We used OPC 53 for a house foundation in Varkala, Kerala (50 metres from the beach). '
            'Within 3 years, we noticed rust stains bleeding through the plaster and hairline cracks '
            'along the RCC columns. Structural engineer confirmed chloride attack on the steel '
            'reinforcement — the OPC concrete absorbed seawater moisture and corroded the bars inside. '
            'Repair estimate: ₹6.5 lakhs. Please use PPC or PSC for anything within 100km of the coast. '
            'OPC 53 is a great cement, but the wrong choice for coastal Kerala.'
        ),
        'reviewer_name': 'Suresh Menon',
        'reviewer_city': 'Varkala',
        'reviewer_state': 'Kerala',
        'reviewer_type': 'contractor',
        'climate_type': 'coastal_humid',
        'use_case': 'RCC foundation and columns, 2-storey house, 50m from coast',
        'helpful_count': 47,
        'is_approved': True,
    },
    {
        'product_name_contains': 'OPC 53',
        'rating': 5,
        'title': 'Excellent for Rajasthan construction — high early strength',
        'review_text': (
            'Built a commercial warehouse in Jodhpur using UltraTech OPC 53. The high early strength '
            '(27 MPa at 3 days) let us strip formwork faster and maintain the construction schedule '
            'despite summer heat. No cracking issues, excellent bond with IS 1786 TMT bars. '
            'The product is excellent — just make sure you are NOT using it near the coast or in '
            'high-rainfall zones. For hot-dry Rajasthan, it is the right choice every time.'
        ),
        'reviewer_name': 'Ramesh Gupta',
        'reviewer_city': 'Jodhpur',
        'reviewer_state': 'Rajasthan',
        'reviewer_type': 'engineer',
        'climate_type': 'hot_dry',
        'use_case': 'Commercial warehouse RCC structure',
        'helpful_count': 31,
        'is_approved': True,
    },

    # ─────────────────────────────────────────────────────────
    # UltraTech PPC — 2 reviews
    # These reinforce the RECOMMENDED ALTERNATIVE in the demo.
    # ─────────────────────────────────────────────────────────
    {
        'product_name_contains': 'UltraTech PPC',
        'rating': 5,
        'title': 'Best cement for coastal Kerala — zero corrosion issues in 5 years',
        'review_text': (
            'Our family home in Kozhikode is 2 km from the Arabian Sea. We used UltraTech PPC '
            'for the entire structure on our structural engineer\'s recommendation after seeing '
            'so many OPC failures nearby. Five years later — no rust stains, no cracks, walls '
            'are pristine. The fly ash content makes the concrete denser and less permeable. '
            'Slightly more expensive than OPC but the peace of mind is worth every rupee. '
            'This is the standard cement for coastal Kerala now, and rightfully so.'
        ),
        'reviewer_name': 'Priya Nair',
        'reviewer_city': 'Kozhikode',
        'reviewer_state': 'Kerala',
        'reviewer_type': 'homeowner',
        'climate_type': 'coastal_humid',
        'use_case': '2-storey family home, 2km from Arabian Sea',
        'helpful_count': 62,
        'is_approved': True,
    },
    {
        'product_name_contains': 'UltraTech PPC',
        'rating': 4,
        'title': 'Go-to cement for all my coastal Kochi projects',
        'review_text': (
            'I have been a contractor in Kochi for 18 years. PPC has been my standard for the '
            'last 8 years for all projects within 50km of the backwaters or coast. The slow '
            'strength gain means you need to plan curing time — do not rush stripping. '
            'But the long-term durability in our saline-humid climate is unmatched among '
            'standard cements. Removing one star only because the price gap with OPC has '
            'widened recently. Still highly recommended for every coastal project.'
        ),
        'reviewer_name': 'Biju Thomas',
        'reviewer_city': 'Kochi',
        'reviewer_state': 'Kerala',
        'reviewer_type': 'contractor',
        'climate_type': 'coastal_humid',
        'use_case': 'Residential and commercial projects, coastal Kochi and backwaters',
        'helpful_count': 53,
        'is_approved': True,
    },

    # ─────────────────────────────────────────────────────────
    # Tata Tiscon Fe 500D — 2 reviews
    # ─────────────────────────────────────────────────────────
    {
        'product_name_contains': 'Tata Tiscon',
        'rating': 5,
        'title': 'Best TMT bar available in India — no compromise on quality',
        'review_text': (
            'As a structural engineer with 22 years of experience, I specify Tata Tiscon Fe 500D '
            'for every project in Zones III and IV. The consistent mechanical properties, '
            'certified elongation of 16%+, and UTS/YS ratio compliance mean the structure '
            'will absorb seismic energy as designed. I have tested samples from 3 different '
            'batches — all passed IS 1786 comfortably with margin. '
            'For coastal projects, specifically request the CRS (Corrosion Resistant Steel) '
            'variant. Slightly higher cost but essential within 5km of coastline.'
        ),
        'reviewer_name': 'Dr. Anand Krishnan',
        'reviewer_city': 'Thiruvananthapuram',
        'reviewer_state': 'Kerala',
        'reviewer_type': 'engineer',
        'climate_type': 'coastal_humid',
        'use_case': 'Multi-storey residential and commercial RCC structures, seismic Zone III',
        'helpful_count': 88,
        'is_approved': True,
    },
    {
        'product_name_contains': 'Tata Tiscon',
        'rating': 5,
        'title': 'Consistent quality across all diameters — highly recommended',
        'review_text': (
            'Used Tata Tiscon Fe 500D for a 3-storey apartment building in Pune. Ordered '
            '8mm, 12mm, 16mm, and 20mm. All diameters had consistent rib pattern, no '
            'mill scale issues, uniform weight. The brand commands a small premium over '
            'local TMT but the consistency is worth it — we never need to worry about '
            'sub-standard material failing an inspection. Delivery was on time from '
            'the authorized distributor.'
        ),
        'reviewer_name': 'Prakash Desai',
        'reviewer_city': 'Pune',
        'reviewer_state': 'Maharashtra',
        'reviewer_type': 'contractor',
        'climate_type': 'heavy_rainfall',
        'use_case': '3-storey apartment building',
        'helpful_count': 41,
        'is_approved': True,
    },

    # ─────────────────────────────────────────────────────────
    # Siporex AAC Blocks — 1 review
    # ─────────────────────────────────────────────────────────
    {
        'product_name_contains': 'Siporex AAC',
        'rating': 5,
        'title': 'Transformed our Ahmedabad home — 40% reduction in AC bills',
        'review_text': (
            'We built our house in Ahmedabad using Siporex AAC blocks for all external walls. '
            'The difference in comfort compared to our old house (which used red clay bricks) '
            'is remarkable. The thermal insulation keeps interiors 4–5°C cooler during peak '
            'summer (45°C outside, 30°C inside without AC running). Our electricity bills for '
            'cooling dropped by nearly 40% in the first summer. The blocks are lightweight '
            'which made construction faster, and the uniform size made for very clean plasterwork. '
            'Initial cost is higher than clay bricks but the energy savings pay it back in 3 years.'
        ),
        'reviewer_name': 'Mihir Shah',
        'reviewer_city': 'Ahmedabad',
        'reviewer_state': 'Gujarat',
        'reviewer_type': 'homeowner',
        'climate_type': 'hot_dry',
        'use_case': '2-storey family home, all external and internal partition walls',
        'helpful_count': 74,
        'is_approved': True,
    },

    # ─────────────────────────────────────────────────────────
    # Kajaria Vitrified Floor Tile — 1 review
    # ─────────────────────────────────────────────────────────
    {
        'product_name_contains': 'Kajaria Vitrified',
        'rating': 5,
        'title': 'Perfect for Kerala — no staining, no watermarks after 3 monsoons',
        'review_text': (
            'Installed Kajaria 600x600 vitrified tiles in our entire ground floor in '
            'Thrissur. Three monsoon seasons later — zero watermarks, zero efflorescence, '
            'zero staining from the humidity. The near-zero water absorption of vitrified '
            'is what makes it the right choice for Kerala. We made the mistake of using '
            'ceramic tiles in our previous house and they started showing hairline surface '
            'cracks and staining within 2 years. Kajaria vitrified has been flawless. '
            'The polished finish stays bright with simple mopping — no waxing or sealing needed.'
        ),
        'reviewer_name': 'Anitha Mathew',
        'reviewer_city': 'Thrissur',
        'reviewer_state': 'Kerala',
        'reviewer_type': 'homeowner',
        'climate_type': 'coastal_humid',
        'use_case': 'Full ground floor of 1800 sqft house',
        'helpful_count': 56,
        'is_approved': True,
    },

    # ─────────────────────────────────────────────────────────
    # Dr. Fixit Powder Waterproof — 1 review
    # ─────────────────────────────────────────────────────────
    {
        'product_name_contains': 'Dr. Fixit Powder',
        'rating': 5,
        'title': 'No more roof leaks after 3 years — integral waterproofing works',
        'review_text': (
            'After suffering roof leakage for 2 consecutive monsoons with a surface-applied '
            'membrane (which eventually peeled), our contractor recommended Dr. Fixit Powder '
            'added into the concrete mix for the terrace slab. Three years of Kerala monsoons '
            '(including one very heavy season with 2 days of continuous rain) — zero seepage. '
            'The integral waterproofing becomes part of the concrete itself so there\'s nothing '
            'to peel, crack, or delaminate. The dose is simple: one 200g packet per 50kg cement '
            'bag. Highly recommended for Kerala terrace slabs and underground water tanks.'
        ),
        'reviewer_name': 'Vineeth Kumar',
        'reviewer_city': 'Palakkad',
        'reviewer_state': 'Kerala',
        'reviewer_type': 'homeowner',
        'climate_type': 'heavy_rainfall',
        'use_case': 'Terrace slab waterproofing, 1800 sqft roof, Kerala',
        'helpful_count': 91,
        'is_approved': True,
    },

]


class Command(BaseCommand):
    help = 'Seed 10 demo reviews with is_approved=True.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing reviews before seeding.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = Review.objects.count()
            Review.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Cleared {count} reviews.'))

        created = skipped = errors = 0

        for data in REVIEWS:
            contains = data.pop('product_name_contains')

            # Find the product by name fragment
            try:
                product = Product.objects.get(name__icontains=contains, is_active=True)
            except Product.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'  ERR  Product containing "{contains}" not found — skipping')
                )
                data['product_name_contains'] = contains  # restore for next run
                errors += 1
                continue
            except Product.MultipleObjectsReturned:
                product = Product.objects.filter(
                    name__icontains=contains, is_active=True
                ).first()

            # Skip if identical title already exists for this product
            if Review.objects.filter(product=product, title=data['title']).exists():
                self.stdout.write(f'  SKIP  {product.name[:40]} — "{data["title"][:40]}"')
                data['product_name_contains'] = contains
                skipped += 1
                continue

            Review.objects.create(product=product, **data)
            self.stdout.write(
                self.style.SUCCESS(f'  ADD   {product.name[:40]} — {data["rating"]}* by {data["reviewer_name"]}')
            )
            created += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done. {created} reviews created, {skipped} skipped, {errors} errors.'
        ))
        self.stdout.write('')
        self.stdout.write('Product aggregate check:')
        for slug_fragment in ['opc-53', 'ppc', 'tiscon']:
            from apps.products.models import Product as P
            p = P.objects.filter(slug__icontains=slug_fragment).first()
            if p:
                self.stdout.write(
                    f'  {p.name[:45]:<45}  avg={p.average_rating}  reviews={p.total_reviews}'
                )
