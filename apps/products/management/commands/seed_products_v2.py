"""
Management command: seed_products_v2
Adds ~50 new products across 5 construction phases.

Usage:
    python manage.py seed_products_v2
    python manage.py seed_products_v2 --clear   (delete v2 products first)

Field mapping verified against models.py:
    brand         = CharField (main brand field)
    manufacturer  = CharField (optional, same as brand for simplicity)
    category      = CharField with CATEGORY_CHOICES codes
    phase         = CharField with PHASE_CHOICES codes
    is_active     = BooleanField (default True — no need to set)
    Images        = ProductImage rows (separate model, image_url URLField)
"""

from django.core.management.base import BaseCommand
from apps.products.models import Product, ProductImage

# Static image URLs — category code → closest existing static file
CATEGORY_IMAGE = {
    'concrete':      '/static/images/products/cement.jpg',
    'hardware':      '/static/images/products/steel.jpg',
    'wood':          '/static/images/products/brick.jpg',
    'roofing':       '/static/images/products/waterproofing.jpg',
    'windows':       '/static/images/products/tile.jpg',
    'plumbing':      '/static/images/products/waterproofing.jpg',
    'electrical':    '/static/images/products/steel.jpg',
    'plaster':       '/static/images/products/cement.jpg',
    'fixtures':      '/static/images/products/tile.jpg',
    # Fallbacks for existing categories used in v2
    'cement':        '/static/images/products/cement.jpg',
    'steel':         '/static/images/products/steel.jpg',
    'brick':         '/static/images/products/brick.jpg',
    'aggregate':     '/static/images/products/aggregate.jpg',
    'waterproofing': '/static/images/products/waterproofing.jpg',
    'tile':          '/static/images/products/tile.jpg',
    'paint':         '/static/images/products/paint.jpg',
}

# Tag all v2 products with this description prefix so --clear can find them
V2_TAG = '[V2]'

PRODUCTS = [
    # ═══════════════════════════════════════════════
    # PHASE 1: FOUNDATION & SUBSTRUCTURE
    # ═══════════════════════════════════════════════
    dict(name='Ready-Mix Concrete M20 Grade', category='concrete',
         price=4800, mrp=5500, unit='cubic metre',
         brand='UltraTech Concrete', is_code='IS 456', phase='foundation',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='M20 grade ready-mix concrete suitable for residential slabs, beams and columns. '
                     'Batched at plant under controlled conditions for consistent quality.'),

    dict(name='Ready-Mix Concrete M25 Grade', category='concrete',
         price=5200, mrp=6000, unit='cubic metre',
         brand='ACC RMC', is_code='IS 456', phase='foundation',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='M25 grade ready-mix concrete for structural elements requiring higher strength. '
                     'Ideal for columns, raft foundations and load-bearing walls.'),

    dict(name='Foundation Anchor Bolts', category='hardware',
         price=180, mrp=220, unit='kg',
         brand='Unbrako', is_code='IS 1367', phase='foundation',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='Heavy-duty galvanised anchor bolts for securing structural steel to concrete foundations. '
                     'Hot-dip galvanised for corrosion resistance in coastal conditions.'),

    dict(name='Blue Metal Aggregate 40mm', category='aggregate',
         price=1400, mrp=1600, unit='metric tonne',
         brand='Blue Metal Quarries', is_code='IS 383', phase='foundation',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='Crushed granite blue metal aggregate (40mm) for PCC and mass concrete works. '
                     'Hard, angular particles improve bond and reduce water demand.'),

    dict(name='Polyethylene Vapour Barrier Sheet', category='waterproofing',
         price=28, mrp=35, unit='sq ft',
         brand='Nilkamal', is_code='IS 2508', phase='foundation',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='500-micron HDPE vapour barrier sheet placed under slabs to prevent '
                     'ground moisture migration. Essential for Kerala high water-table sites.'),

    dict(name='Ready-to-Use Masonry Mortar', category='cement',
         price=320, mrp=380, unit='bag (50kg)',
         brand='Weber Saint-Gobain', is_code='IS 2250', phase='foundation',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='Pre-blended polymer-modified masonry mortar. Just add water. '
                     'Superior bond strength and workability over site-mixed mortar.'),

    dict(name='Laterite Stone Block', category='brick',
         price=25, mrp=32, unit='piece',
         brand='Kerala Local Quarries', is_code='IS 3620', phase='foundation',
         coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='Traditional Kerala laterite (chuvanna kallu) block for load-bearing walls. '
                     'Naturally breathable and thermally comfortable in humid coastal climates.'),

    dict(name='Plain Cement Concrete M10 Mix', category='concrete',
         price=3800, mrp=4500, unit='cubic metre',
         brand='Local RMC Plants', is_code='IS 456', phase='foundation',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='M10 lean concrete for levelling course, blinding layers and non-structural fills. '
                     'Available from local batching plants across Kerala.'),

    # ═══════════════════════════════════════════════
    # PHASE 2: FRAMING & STRUCTURE
    # ═══════════════════════════════════════════════
    dict(name='Steel I-Beam ISMB 200', category='steel',
         price=68, mrp=78, unit='kg',
         brand='SAIL', is_code='IS 2062', phase='framing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='SAIL hot-rolled I-beam (ISMB 200) for secondary beams, lintels and '
                     'mezzanine floors. Grade E250 mild steel per IS 2062.'),

    dict(name='Steel Channel ISMC 150', category='steel',
         price=65, mrp=75, unit='kg',
         brand='Tata Steel', is_code='IS 2062', phase='framing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='Tata Steel hot-rolled channel section (ISMC 150) for purlin, '
                     'girt and secondary framing members. Grade E250.'),

    dict(name='Binding Wire 18 Gauge', category='hardware',
         price=75, mrp=90, unit='kg',
         brand='Tata Wiron', is_code='IS 280', phase='framing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='Annealed mild steel binding wire for tying reinforcement bars. '
                     'Soft and pliable for easy tying without breaking.'),

    dict(name='Greenply BWR Plywood 18mm', category='wood',
         price=95, mrp=115, unit='sq ft',
         brand='Greenply', is_code='IS 303', phase='framing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='Boiling Water Resistant (BWR) plywood for shuttering, furniture and '
                     'general construction. Phenol formaldehyde bonded for high moisture resistance.'),

    dict(name='Shuttering Plywood 12mm', category='wood',
         price=55, mrp=68, unit='sq ft',
         brand='Century Plyboards', is_code='IS 4990', phase='framing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='Phenolic film-faced shuttering plywood for concrete formwork. '
                     'Smooth face gives clean concrete finish. Reusable 8-10 times.'),

    dict(name='Welded Wire Mesh 4mm', category='steel',
         price=82, mrp=95, unit='sq metre',
         brand='JSW Steel', is_code='IS 1566', phase='framing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='Pre-welded reinforcement mesh (150x150mm grid, 4mm wire) for slabs, '
                     'walls and ground beams. Saves site labour vs tying individual bars.'),

    dict(name='Structural Steel Plate 6mm', category='steel',
         price=72, mrp=85, unit='kg',
         brand='SAIL', is_code='IS 2062', phase='framing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='6mm mild steel plate (Grade E250) for base plates, gussets and '
                     'connection plates in structural steel work.'),

    dict(name='Concrete Cover Blocks 40mm', category='concrete',
         price=4, mrp=6, unit='piece',
         brand='Local Precast', is_code='IS 456', phase='framing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='Precast concrete spacer blocks (cover blocks) to maintain correct '
                     'cover to reinforcement per IS 456. 40mm clear cover for beams and columns.'),

    # ═══════════════════════════════════════════════
    # PHASE 3: EXTERIOR & ROOFING
    # ═══════════════════════════════════════════════
    dict(name='Mangalore Clay Roof Tile', category='roofing',
         price=28, mrp=35, unit='piece',
         brand='Mangalore Tiles Co.', is_code='IS 654', phase='exterior',
         coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='Traditional Mangalore pattern interlocking clay roof tiles. '
                     'Natural clay composition ideal for Kerala climate — breathable, '
                     'keeps interiors cool and withstands heavy monsoon rainfall.'),

    dict(name='Galvalume Roofing Sheet 0.5mm', category='roofing',
         price=420, mrp=500, unit='sq metre',
         brand='JSW Steel', is_code='IS 277', phase='exterior',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='Galvalume (zinc-aluminium alloy coated) steel roofing sheet 0.5mm thick. '
                     'Superior corrosion resistance vs plain GI. Rated for high wind zones.'),

    dict(name='UPVC Sliding Window 2-Track', category='windows',
         price=650, mrp=800, unit='sq ft',
         brand='Fenesta', is_code='IS 14856', phase='exterior',
         coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='White UPVC 2-track sliding window with 5mm float glass. '
                     'UV-stabilised UPVC resists salt air corrosion — ideal for coastal Kerala.'),

    dict(name='Aluminium Casement Window', category='windows',
         price=550, mrp=680, unit='sq ft',
         brand='Jindal Aluminium', is_code='IS 1948', phase='exterior',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='Powder-coated aluminium casement window with EPDM weather seal. '
                     'Anodised finish available for extra corrosion protection in coastal areas.'),

    dict(name='Solid Core Flush Door 32mm', category='windows',
         price=4800, mrp=5800, unit='piece',
         brand='Greenply', is_code='IS 2202', phase='exterior',
         coastal_humid=True, heavy_rainfall=True,
         description='32mm thick solid core flush door with BWR plywood core and '
                     'teak veneer face. Moisture-resistant adhesive bonding throughout.'),

    dict(name='Godrej Steel Security Door', category='windows',
         price=12000, mrp=15000, unit='piece',
         brand='Godrej', is_code='IS 4962', phase='exterior',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='Heavy-duty galvanised steel security door with 3-point locking mechanism. '
                     'Powder-coated for corrosion resistance. Rated for cyclone wind loads.'),

    dict(name='Roofing Underlayment Felt', category='roofing',
         price=22, mrp=28, unit='sq ft',
         brand='STP Limited', is_code='IS 1322', phase='exterior',
         coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='Bituminous felt underlay laid under roof tiles to provide secondary '
                     'waterproofing. Essential for Kerala high-rainfall zones.'),

    dict(name='PVC Rainwater Gutter 110mm', category='plumbing',
         price=185, mrp=220, unit='metre',
         brand='Astral Pipes', is_code='IS 13592', phase='exterior',
         coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='110mm dia PVC rainwater downpipe and gutter system. '
                     'UV-stabilised grey PVC for outdoor installation. Easy push-fit joints.'),

    dict(name='Polymer Modified Exterior Plaster', category='plaster',
         price=420, mrp=500, unit='bag (30kg)',
         brand='Weber Saint-Gobain', is_code='IS 2542', phase='exterior',
         coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='Polymer-modified cement plaster for external walls. '
                     'Crack-resistant and water-repellent. Ideal for Kerala coastal exposure.'),

    # ═══════════════════════════════════════════════
    # PHASE 4: ROUGH-IN (PLUMBING & ELECTRICAL)
    # ═══════════════════════════════════════════════
    dict(name='CPVC Hot & Cold Water Pipe 25mm', category='plumbing',
         price=145, mrp=175, unit='metre',
         brand='Astral Pipes', is_code='IS 15778', phase='roughin',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='25mm CPVC pipe for hot and cold water supply lines. '
                     'Rated to 93°C. No corrosion, no scale build-up. Chlorine-resistant.'),

    dict(name='PVC SWR Drainage Pipe 110mm', category='plumbing',
         price=220, mrp=260, unit='metre',
         brand='Finolex Pipes', is_code='IS 13592', phase='roughin',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='110mm dia PVC soil, waste and rain (SWR) pipe for internal drainage. '
                     'Orange colour-coded. Ring-fit rubber seal joints.'),

    dict(name='uPVC Borewell Column Pipe 100mm', category='plumbing',
         price=380, mrp=450, unit='metre',
         brand='Prince Pipes', is_code='IS 12818', phase='roughin',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='100mm uPVC column pipe for submersible pump installations. '
                     'Threaded ends for easy assembly. UV-stabilised for exposed sections.'),

    dict(name='Sintex Water Storage Tank 1000L', category='plumbing',
         price=4800, mrp=5800, unit='piece',
         brand='Sintex', is_code='IS 12701', phase='roughin',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='1000-litre triple-layer insulated water tank. Anti-algal inner layer. '
                     'Black outer layer blocks UV. Loft-mountable with reinforced lid.'),

    dict(name='Overhead Water Tank 500L PVC', category='plumbing',
         price=2800, mrp=3400, unit='piece',
         brand='Penguin Tanks', is_code='IS 12701', phase='roughin',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='500-litre double-layer PVC overhead tank. '
                     'Food-grade inner surface. Suitable for terrace mounting. ISI marked.'),

    dict(name='Finolex Copper Wire 2.5 sq mm', category='electrical',
         price=85, mrp=100, unit='metre',
         brand='Finolex Cables', is_code='IS 694', phase='roughin',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='2.5 sq mm FR PVC insulated copper wire for power circuits. '
                     'ISI marked. FR grade insulation self-extinguishes if ignited.'),

    dict(name='Polycab Copper Wire 4 sq mm', category='electrical',
         price=140, mrp=165, unit='metre',
         brand='Polycab', is_code='IS 694', phase='roughin',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='4 sq mm FR FRLSH copper wire for AC, water heater and high-load circuits. '
                     'Low-smoke halogen-free insulation for enclosed conduits.'),

    dict(name='PVC Conduit Pipe 25mm', category='electrical',
         price=38, mrp=48, unit='metre',
         brand='Ashok Electrical', is_code='IS 9537', phase='roughin',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='25mm ISI marked PVC conduit pipe for concealed wiring. '
                     'Heavy-duty 2mm wall. Impact resistant and self-extinguishing.'),

    dict(name='Legrand MCB Distribution Board 8-Way', category='electrical',
         price=2200, mrp=2800, unit='piece',
         brand='Legrand', is_code='IS 8623', phase='roughin',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='8-way single-phase MCB distribution board with neutral bar and '
                     'earth bar. IP40 surface-mount enclosure. DIN rail for MCBs and RCCBs.'),

    dict(name='Schneider Electric MCB 20A', category='electrical',
         price=280, mrp=350, unit='piece',
         brand='Schneider Electric', is_code='IS 60898', phase='roughin',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='20A single-pole miniature circuit breaker (Type C curve) for '
                     'general lighting and power circuits. 6kA short-circuit capacity.'),

    dict(name='GI Junction Box 4x4 inch', category='electrical',
         price=55, mrp=70, unit='piece',
         brand='Elmex', is_code='IS 5133', phase='roughin',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='Galvanised iron surface-mount junction box (4x4 inch) for '
                     'cable terminations and splices. Knock-out entries on all sides.'),

    dict(name='PVC Concealed Conduit 20mm', category='electrical',
         price=22, mrp=28, unit='metre',
         brand='Polycab', is_code='IS 9537', phase='roughin',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='20mm thin-wall ISI PVC conduit for concealed wiring in walls. '
                     'Flexible enough for bends without cutting. Use with 1.5-2.5 sq mm wire.'),

    dict(name='Prefab Concrete Septic Tank 1000L', category='plumbing',
         price=18000, mrp=22000, unit='piece',
         brand='Local Precast Kerala', is_code='IS 2470', phase='roughin',
         coastal_humid=True, heavy_rainfall=True,
         description='Precast reinforced concrete septic tank (1000L capacity) with '
                     'two-chamber design per IS 2470. Covers with manhole access. '
                     'Suitable for Kerala high water-table conditions.'),

    # ═══════════════════════════════════════════════
    # PHASE 5: INTERIOR FINISHING
    # ═══════════════════════════════════════════════
    dict(name='Saint-Gobain Gypsum Board 12.5mm', category='plaster',
         price=38, mrp=48, unit='sq ft',
         brand='Saint-Gobain Gyproc', is_code='IS 2095', phase='finishing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='Standard 12.5mm gypsum board for false ceilings and partition walls. '
                     'Type A regular board. Use moisture-resistant (MR) board in wet areas.'),

    dict(name='Gypsum Internal Wall Plaster', category='plaster',
         price=380, mrp=450, unit='bag (25kg)',
         brand='Birla Putty', is_code='IS 2542', phase='finishing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='Ready-to-use gypsum finish plaster for internal walls. '
                     'Single-coat application to 12mm. Smooth finish without putty.'),

    dict(name='Asian Paints Wall Putty', category='paint',
         price=22, mrp=28, unit='kg',
         brand='Asian Paints', is_code='IS 15477', phase='finishing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='White cement-based wall putty for filling hairline cracks and '
                     'levelling wall surface before painting. ISI marked.'),

    dict(name='Pergo Laminate Flooring 8mm AC3', category='tile',
         price=85, mrp=110, unit='sq ft',
         brand='Pergo', is_code='IS 14587', phase='finishing',
         hot_dry=True, cold_hilly=True,
         description='8mm AC3 grade laminate flooring with click-lock installation. '
                     'Not recommended for wet or humid areas. Best for bedrooms and living rooms '
                     'in dry climates.'),

    dict(name='Laticrete Epoxy Tile Grout', category='tile',
         price=320, mrp=400, unit='kg',
         brand='Laticrete', is_code='IS 12212', phase='finishing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='2-component epoxy grout for joints in wet areas, kitchen counters '
                     'and swimming pools. Stain-proof, mould-proof, chemical-resistant.'),

    dict(name='Johnson Ceramic Wall Tile 300x450mm', category='tile',
         price=42, mrp=55, unit='sq ft',
         brand='Johnson Tiles', is_code='IS 13630', phase='finishing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='Vitrified ceramic wall tile (300x450mm) for bathrooms and kitchens. '
                     'Water absorption <10% per IS 13630. Various glaze options available.'),

    dict(name='Teak Wooden Door Frame', category='wood',
         price=3200, mrp=4000, unit='piece',
         brand='Kerala Timber Depot', is_code='IS 4021', phase='finishing',
         coastal_humid=True, heavy_rainfall=True,
         description='Teak wood door frame (100x75mm section) for main entrance. '
                     'Naturally resistant to moisture and termites. Kerala origin teak.'),

    dict(name='Aluminium Door Frame', category='windows',
         price=1800, mrp=2200, unit='piece',
         brand='Jindal Aluminium', is_code='IS 1948', phase='finishing',
         coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='Extruded aluminium door frame (anodised silver finish) for '
                     'internal and external doors. Corrosion-proof. No warping or swelling.'),

    dict(name='Sleek Modular Kitchen Cabinet per Linear Ft', category='fixtures',
         price=2800, mrp=3500, unit='linear ft',
         brand='Sleek Kitchens', is_code='', phase='finishing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='18mm BWR plywood carcase with UV-coated shutter. '
                     'Soft-close hinges and drawer channels. Kerala-adapted moisture-resistant finish.'),

    dict(name='Black Galaxy Granite Countertop', category='tile',
         price=220, mrp=280, unit='sq ft',
         brand='Rajasthan Granites', is_code='IS 3316', phase='finishing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='Polished Black Galaxy granite (25mm thick) for kitchen and bathroom countertops. '
                     'Naturally heat and stain resistant. Available in Kerala from local stockists.'),

    dict(name='Philips LED Batten 18W', category='electrical',
         price=420, mrp=520, unit='piece',
         brand='Philips', is_code='IS 16102', phase='finishing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='18W LED batten light (neutral white 4000K, 1700 lumens). '
                     'IP20, lifespan >25,000 hours. Direct replacement for 36W fluorescent.'),

    dict(name='Legrand Modular Switch 6A', category='electrical',
         price=280, mrp=350, unit='piece',
         brand='Legrand', is_code='IS 3854', phase='finishing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='Legrand Arteor 6A one-way switch in white finish. '
                     'Piano key mechanism, child-safe shutters on socket.'),

    dict(name='Kohler Wall-Hung WC', category='plumbing',
         price=8500, mrp=11000, unit='piece',
         brand='Kohler', is_code='IS 2556', phase='finishing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='Kohler wall-hung water closet with concealed cistern carrier frame. '
                     'Dual-flush 3/6L. Rimless design for easy cleaning. UF seat included.'),

    dict(name='Hindware Tabletop Wash Basin', category='plumbing',
         price=2800, mrp=3500, unit='piece',
         brand='Hindware', is_code='IS 2556', phase='finishing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True, cyclone_prone=True,
         description='Vitreous china tabletop wash basin (560x460mm). '
                     'Pre-drilled single tap hole. FSSL and WaterMark certified.'),

    dict(name='Jaquar CP Bath Fittings Set', category='plumbing',
         price=3200, mrp=4000, unit='set',
         brand='Jaquar', is_code='IS 1795', phase='finishing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='Complete CP (chrome-plated brass) bath set: overhead shower, '
                     'hand shower with hose, thermostatic diverter and bath filler.'),

    dict(name='Nirali SS Double Bowl Kitchen Sink', category='plumbing',
         price=4500, mrp=5800, unit='piece',
         brand='Nirali', is_code='IS 13983', phase='finishing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='304-grade stainless steel double bowl kitchen sink (900x450mm). '
                     'Satin finish. 0.8mm thick. Includes waste fittings and mounting clips.'),

    dict(name='Somany Ceramic Skirting Tile 80x300mm', category='tile',
         price=35, mrp=48, unit='sq ft',
         brand='Somany Ceramics', is_code='IS 13630', phase='finishing',
         hot_dry=True, coastal_humid=True, heavy_rainfall=True,
         description='80x300mm ceramic skirting tile to finish wall-floor junction. '
                     'Matches standard floor tile glaze lines. Easy mitre-cut installation.'),
]


class Command(BaseCommand):
    help = 'Seed 50 new products across 5 construction phases (V2 expansion)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all V2 products before re-seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = Product.objects.filter(
                description__startswith=V2_TAG
            ).delete()
            self.stdout.write(f'Cleared {deleted} V2 products.')

        added = skipped = 0

        for p in PRODUCTS:
            name = p['name']
            slug_check = name  # Product.save() auto-generates slug

            if Product.objects.filter(name=name).exists():
                self.stdout.write(f'  SKIP (exists): {name}')
                skipped += 1
                continue

            product = Product.objects.create(
                name=name,
                brand=p['brand'],
                manufacturer=p['brand'],
                category=p['category'],
                description=V2_TAG + ' ' + p['description'],
                price=p['price'],
                mrp=p['mrp'],
                unit=p['unit'],
                is_code=p.get('is_code', ''),
                phase=p.get('phase', ''),
                hot_dry=p.get('hot_dry', False),
                coastal_humid=p.get('coastal_humid', False),
                heavy_rainfall=p.get('heavy_rainfall', False),
                cold_hilly=p.get('cold_hilly', False),
                cyclone_prone=p.get('cyclone_prone', False),
                price_source='seed_baseline',
                price_confidence='medium',
            )

            # Create a ProductImage row using the static image URL
            image_url = CATEGORY_IMAGE.get(p['category'], '/static/images/products/cement.jpg')
            ProductImage.objects.create(
                product=product,
                image_url=image_url,
                is_primary=True,
                caption=p['brand'],
            )

            self.stdout.write(f'  ADDED: {name}')
            added += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Added: {added}  Skipped: {skipped}'
        ))

        total = Product.objects.filter(is_active=True).count()
        self.stdout.write(f'Total active products: {total}')

        for phase_code, phase_label in Product.PHASE_CHOICES:
            count = Product.objects.filter(phase=phase_code, is_active=True).count()
            self.stdout.write(f'  {phase_label}: {count}')

        no_phase = Product.objects.filter(phase='', is_active=True).count()
        self.stdout.write(f'  (no phase assigned): {no_phase}')
