"""
management/commands/seed_products.py

Populates the database with 30 realistic Indian construction materials
for demo and development purposes.

Usage:
    python manage.py seed_products          # add all, skip existing slugs
    python manage.py seed_products --clear  # wipe products table first, then seed

DEMO-CRITICAL products (the climate filter killer feature):
  - UltraTech OPC 53: coastal_humid=False  ← shows the WARNING banner
  - UltraTech PPC:    coastal_humid=True   ← shows as the RECOMMENDED alternative

30 products across 7 categories:
  Cement (6), Steel (5), Brick (5), Sand/Aggregate (4),
  Tile (5), Paint (3), Waterproofing (2)
"""

from django.core.management.base import BaseCommand
from apps.products.models import Product, ProductImage


# ─── Product data ──────────────────────────────────────────────────────────────
# Each dict maps directly to Product model fields.
# Climate fields: True = suitable, False = not suitable / not tested.
# Prices: realistic Indian market rates as of 2025-26.

PRODUCTS = [

    # ═══════════════════════════════════════════
    # CEMENT (6 products)
    # Demo contrast: OPC 53 (bad coast) vs PPC (good coast)
    # ═══════════════════════════════════════════

    {
        'name': 'UltraTech OPC 53 Grade Cement',
        'brand': 'UltraTech Cement',
        'manufacturer': 'UltraTech Cement Limited',
        'category': 'cement',
        'subcategory': 'OPC 53 Grade',
        'is_code': 'IS 12269',
        'description': (
            'UltraTech OPC 53 Grade is India\'s most trusted high-strength cement, '
            'used for RCC structures, precast elements, and prestressed concrete. '
            'Its high compressive strength makes it ideal for multi-storey buildings, '
            'bridges, and industrial floors in dry and temperate climates.\n\n'
            'IMPORTANT: OPC 53 has low resistance to chloride and sulfate attack. '
            'It is NOT recommended for coastal regions, areas with high groundwater '
            'sulfate content, or cyclone-prone coastlines. Coastal exposure accelerates '
            'corrosion of steel reinforcement inside OPC concrete, leading to structural '
            'damage within 5–10 years.'
        ),
        'price': 380,
        'mrp': 420,
        'unit': 'bag (50 kg)',
        # ── Climate suitability ──
        'hot_dry': True,       # Works fine in hot-dry (Rajasthan, Gujarat interior)
        'coastal_humid': False, # ⚠️ DEMO KEY: chloride attack risk on coast
        'heavy_rainfall': False, # Low sulfate resistance — risky in waterlogged areas
        'cold_hilly': True,    # Good in cold climates (high early strength)
        'cyclone_prone': False, # Not for cyclone zones (coastal = chloride attack)
        # ── Regional ──
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh',
                             'Maharashtra', 'Gujarat', 'Rajasthan', 'UP', 'Delhi NCR'],
        'seismic_zone': 'III',
        'regional_notes': (
            'Widely available across India. Avoid in coastal Kerala, Konkan coast, '
            'Odisha, and West Bengal coastal districts. For those regions, use PPC '
            'or Portland Slag Cement instead.'
        ),
        'specifications': {
            'Grade': 'OPC 53',
            'IS Code': 'IS 12269:2013',
            'Compressive Strength (3 day)': '27 MPa min',
            'Compressive Strength (28 day)': '53 MPa min',
            'Initial Setting Time': '30 minutes min',
            'Final Setting Time': '600 minutes max',
            'Fineness': '225 m²/kg min',
            'Soundness (Le Chatelier)': '10 mm max',
            'Bag Weight': '50 kg',
        },
        'average_rating': 4.4,
        'total_reviews': 128,
    },

    {
        'name': 'UltraTech PPC (Portland Pozzolana Cement)',
        'brand': 'UltraTech Cement',
        'manufacturer': 'UltraTech Cement Limited',
        'category': 'cement',
        'subcategory': 'PPC',
        'is_code': 'IS 1489',
        'description': (
            'UltraTech PPC blends OPC clinker with fly ash (15–35%), producing a cement '
            'with superior durability in aggressive environments. The pozzolanic reaction '
            'produces less calcium hydroxide, dramatically reducing chloride permeability.\n\n'
            'RECOMMENDED for coastal Kerala, Konkan, Odisha, and all cyclone-prone '
            'coastlines. Also excellent for mass concrete (dams, raft foundations) due '
            'to lower heat of hydration. Slow-gaining strength makes it ideal for '
            'hot-weather and heavy-rainfall construction where cracking is a concern.'
        ),
        'price': 360,
        'mrp': 400,
        'unit': 'bag (50 kg)',
        # ── Climate suitability ──
        'hot_dry': True,        # Fine in hot-dry; low heat of hydration is a bonus
        'coastal_humid': True,  # ✅ DEMO KEY: excellent chloride resistance
        'heavy_rainfall': True, # Low permeability = good in waterlogged/rain areas
        'cold_hilly': False,    # Slow strength gain problematic in freezing temps
        'cyclone_prone': True,  # Chloride resistance handles saline coastal air
        # ── Regional ──
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh',
                             'Goa', 'Maharashtra', 'Odisha', 'West Bengal'],
        'seismic_zone': 'III',
        'regional_notes': (
            'First choice for all construction within 50 km of India\'s coastline. '
            'Particularly recommended for Kerala (Thiruvananthapuram, Kochi, Kozhikode) '
            'and Konkan coast (Mumbai, Goa, Mangalore).'
        ),
        'specifications': {
            'Grade': 'PPC (Fly Ash Based)',
            'IS Code': 'IS 1489 (Part 1):1991',
            'Fly Ash Content': '15–35%',
            'Compressive Strength (28 day)': '33 MPa min',
            'Initial Setting Time': '30 minutes min',
            'Final Setting Time': '600 minutes max',
            'Fineness': '300 m²/kg min',
            'Bag Weight': '50 kg',
        },
        'average_rating': 4.6,
        'total_reviews': 214,
    },

    {
        'name': 'ACC Gold OPC 43 Grade Cement',
        'brand': 'ACC Limited',
        'manufacturer': 'ACC Limited (Holcim Group)',
        'category': 'cement',
        'subcategory': 'OPC 43 Grade',
        'is_code': 'IS 8112',
        'description': (
            'ACC Gold OPC 43 Grade is a general-purpose cement suited for plastering, '
            'brickwork, flooring, and moderate RCC construction. Lower strength than '
            'OPC 53 but more workable and economical for non-structural applications. '
            'Preferred by masons for finishing work due to its smooth texture.'
        ),
        'price': 355,
        'mrp': 390,
        'unit': 'bag (50 kg)',
        'hot_dry': True,
        'coastal_humid': False,
        'heavy_rainfall': False,
        'cold_hilly': True,
        'cyclone_prone': False,
        'states_available': ['Maharashtra', 'Gujarat', 'Rajasthan', 'MP', 'UP', 'Delhi NCR'],
        'seismic_zone': 'III',
        'specifications': {
            'Grade': 'OPC 43',
            'IS Code': 'IS 8112:2013',
            'Compressive Strength (28 day)': '43 MPa min',
            'Initial Setting Time': '30 minutes min',
            'Bag Weight': '50 kg',
        },
        'average_rating': 4.2,
        'total_reviews': 89,
    },

    {
        'name': 'Ramco Sulphate Resistant Cement',
        'brand': 'Ramco Cements',
        'manufacturer': 'The Ramco Cements Limited',
        'category': 'cement',
        'subcategory': 'SRC',
        'is_code': 'IS 12330',
        'description': (
            'Ramco SRC is formulated with low C3A content, making it highly resistant '
            'to sulfate attack from soil and groundwater. Essential for foundations in '
            'black cotton soil zones (Deccan Plateau) and marine substructures. '
            'Widely used in wastewater treatment plants, coastal foundations, and '
            'industrial floors exposed to chemicals.'
        ),
        'price': 440,
        'mrp': 480,
        'unit': 'bag (50 kg)',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': False,
        'cyclone_prone': True,
        'states_available': ['Tamil Nadu', 'Andhra Pradesh', 'Karnataka', 'Telangana'],
        'seismic_zone': 'II',
        'regional_notes': 'Especially recommended for black cotton soil regions of the Deccan Plateau.',
        'specifications': {
            'IS Code': 'IS 12330:1988',
            'C3A Content': '< 3.5%',
            'Compressive Strength (28 day)': '33 MPa min',
            'Sulfate Resistance': 'High',
            'Bag Weight': '50 kg',
        },
        'average_rating': 4.5,
        'total_reviews': 61,
    },

    {
        'name': 'Dalmia PSC (Portland Slag Cement)',
        'brand': 'Dalmia Bharat Cement',
        'manufacturer': 'Dalmia Bharat Limited',
        'category': 'cement',
        'subcategory': 'PSC',
        'is_code': 'IS 455',
        'description': (
            'Dalmia PSC uses Ground Granulated Blast Furnace Slag (GGBFS) — a steel '
            'industry byproduct — to create an eco-friendly cement with outstanding '
            'durability. GGBFS dramatically reduces chloride permeability and sulfate '
            'vulnerability. Top choice for marine structures, sewage treatment, and '
            'all coastal construction. Slower strength gain than OPC makes it ideal '
            'for mass concrete to reduce thermal cracking.'
        ),
        'price': 370,
        'mrp': 410,
        'unit': 'bag (50 kg)',
        'hot_dry': False,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': False,
        'cyclone_prone': True,
        'states_available': ['Odisha', 'West Bengal', 'Tamil Nadu', 'Andhra Pradesh', 'Kerala'],
        'seismic_zone': 'III',
        'specifications': {
            'IS Code': 'IS 455:2015',
            'Slag Content': '25–70%',
            'Compressive Strength (28 day)': '33 MPa min',
            'Chloride Permeability': 'Very Low',
            'Bag Weight': '50 kg',
        },
        'average_rating': 4.3,
        'total_reviews': 47,
    },

    {
        'name': 'Birla White Cement',
        'brand': 'Birla White',
        'manufacturer': 'UltraTech Cement Limited (Birla White brand)',
        'category': 'cement',
        'subcategory': 'White Cement',
        'is_code': 'IS 8042',
        'description': (
            'Birla White is India\'s most popular white cement, used exclusively for '
            'aesthetic finishing — white putty, textured finishes, tile grouting, '
            'and decorative plasterwork. It is NOT a structural cement; never use '
            'it as a substitute for OPC or PPC in load-bearing applications. '
            'Produces brilliant white colour with high reflectivity.'
        ),
        'price': 850,
        'mrp': 920,
        'unit': 'bag (25 kg)',
        # Decorative/finishing product — climate flags reflect that it CAN be
        # applied in any climate as a finishing coat, but it is NOT a structural
        # cement and should NOT appear as an alternative to OPC/PPC.
        'hot_dry': True,
        'coastal_humid': False,  # Decorative only — not a structural recommendation
        'heavy_rainfall': False,
        'cold_hilly': True,
        'cyclone_prone': False,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh',
                             'Maharashtra', 'Gujarat', 'Delhi NCR', 'UP'],
        'seismic_zone': None,
        'specifications': {
            'IS Code': 'IS 8042:1989',
            'Whiteness': '> 85%',
            'Compressive Strength (28 day)': '33 MPa min',
            'Use': 'Decorative / Finishing only — NOT structural',
            'Bag Weight': '25 kg',
        },
        'average_rating': 4.7,
        'total_reviews': 183,
    },

    # ═══════════════════════════════════════════
    # STEEL — TMT BARS (5 products)
    # ═══════════════════════════════════════════

    {
        'name': 'Tata Tiscon Fe 500D TMT Bars',
        'brand': 'Tata Steel',
        'manufacturer': 'Tata Steel Limited',
        'category': 'steel',
        'subcategory': 'TMT Bars',
        'is_code': 'IS 1786',
        'description': (
            'Tata Tiscon Fe 500D is the gold standard of Indian TMT reinforcement. '
            'The "D" suffix signifies superior ductility — critical in earthquake-prone '
            'zones where the structure must absorb seismic energy without brittle fracture. '
            'Thermo-mechanically treated for a hard outer martensite ring with a tough '
            'ferrite-pearlite core. Ribbed surface ensures superior bond with concrete.\n\n'
            'The corrosion-resistant grade is especially recommended for coastal Kerala, '
            'Goa, and Andhra Pradesh where saline air accelerates bar corrosion.'
        ),
        'price': 58000,
        'mrp': 62000,
        'unit': 'metric tonne',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh',
                             'Maharashtra', 'Delhi NCR', 'UP', 'Bihar', 'West Bengal'],
        'seismic_zone': 'IV',
        'regional_notes': 'CRS (Corrosion Resistant Steel) variant recommended for coastal districts.',
        'specifications': {
            'IS Code': 'IS 1786:2008',
            'Grade': 'Fe 500D',
            'Yield Strength': '500 MPa min',
            'UTS': '600 MPa min',
            'Elongation': '16% min',
            'UTS/YS Ratio': '1.15 min',
            'Available Diameters': '8mm, 10mm, 12mm, 16mm, 20mm, 25mm, 32mm',
        },
        'average_rating': 4.8,
        'total_reviews': 342,
    },

    {
        'name': 'SAIL TMT Fe 415 Bars',
        'brand': 'SAIL (Steel Authority of India)',
        'manufacturer': 'Steel Authority of India Limited',
        'category': 'steel',
        'subcategory': 'TMT Bars',
        'is_code': 'IS 1786',
        'description': (
            'SAIL TMT Fe 415 from India\'s largest public-sector steel company. '
            'Fe 415 grade is the minimum recommended for RCC construction per IS 456. '
            'Higher ductility than Fe 500, making it more forgiving in seismic events. '
            'Economical choice for residential construction in low-seismic zones.'
        ),
        'price': 54000,
        'mrp': 58000,
        'unit': 'metric tonne',
        'hot_dry': True,
        'coastal_humid': False,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': False,
        'states_available': ['Delhi NCR', 'UP', 'Bihar', 'Jharkhand', 'West Bengal',
                             'Odisha', 'MP', 'Rajasthan'],
        'seismic_zone': 'III',
        'specifications': {
            'IS Code': 'IS 1786:2008',
            'Grade': 'Fe 415',
            'Yield Strength': '415 MPa min',
            'UTS': '485 MPa min',
            'Elongation': '14.5% min',
            'Available Diameters': '8mm, 10mm, 12mm, 16mm, 20mm, 25mm, 32mm',
        },
        'average_rating': 4.3,
        'total_reviews': 156,
    },

    {
        'name': 'JSW Neosteel Fe 550D TMT Bars',
        'brand': 'JSW Steel',
        'manufacturer': 'JSW Steel Limited',
        'category': 'steel',
        'subcategory': 'TMT Bars',
        'is_code': 'IS 1786',
        'description': (
            'JSW Neosteel Fe 550D is a high-strength TMT bar for demanding structural '
            'applications — high-rise buildings, flyovers, bridges. The 550 MPa yield '
            'strength allows engineers to use smaller bar diameters, reducing steel '
            'consumption by up to 10% compared to Fe 415. "D" grade ensures ductility '
            'requirements are met for seismic zones III and IV.'
        ),
        'price': 61000,
        'mrp': 65000,
        'unit': 'metric tonne',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Maharashtra', 'Karnataka', 'Goa', 'Andhra Pradesh',
                             'Telangana', 'Gujarat'],
        'seismic_zone': 'IV',
        'specifications': {
            'IS Code': 'IS 1786:2008',
            'Grade': 'Fe 550D',
            'Yield Strength': '550 MPa min',
            'UTS': '660 MPa min',
            'Elongation': '14.5% min',
            'Available Diameters': '8mm, 10mm, 12mm, 16mm, 20mm, 25mm, 32mm',
        },
        'average_rating': 4.6,
        'total_reviews': 98,
    },

    {
        'name': 'Kamdhenu Fe 500D TMT Bars',
        'brand': 'Kamdhenu Limited',
        'manufacturer': 'Kamdhenu Limited',
        'category': 'steel',
        'subcategory': 'TMT Bars',
        'is_code': 'IS 1786',
        'description': (
            'Kamdhenu TMT is a popular choice in North India\'s residential market. '
            'Fe 500D grade with corrosion-resistant coating option. Strong franchised '
            'distribution network means availability even in Tier-3 cities. Quality '
            'certifications from Bureau of Indian Standards (BIS).'
        ),
        'price': 55500,
        'mrp': 60000,
        'unit': 'metric tonne',
        'hot_dry': True,
        'coastal_humid': False,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': False,
        'states_available': ['UP', 'Delhi NCR', 'Rajasthan', 'Haryana', 'Punjab',
                             'HP', 'Uttarakhand', 'Bihar'],
        'seismic_zone': 'IV',
        'specifications': {
            'IS Code': 'IS 1786:2008',
            'Grade': 'Fe 500D',
            'Yield Strength': '500 MPa min',
            'UTS': '600 MPa min',
            'Elongation': '16% min',
        },
        'average_rating': 4.1,
        'total_reviews': 73,
    },

    {
        'name': 'Vizag Steel Fe 415 TMT Bars',
        'brand': 'Rashtriya Ispat Nigam (Vizag Steel)',
        'manufacturer': 'Rashtriya Ispat Nigam Limited',
        'category': 'steel',
        'subcategory': 'TMT Bars',
        'is_code': 'IS 1786',
        'description': (
            'Vizag Steel TMT bars are manufactured at the Visakhapatnam Steel Plant, '
            'India\'s only shore-based integrated steel plant. Excellent quality control '
            'with in-house raw material processing. Preferred in Andhra Pradesh, '
            'Telangana, and Odisha construction projects.'
        ),
        'price': 53500,
        'mrp': 57000,
        'unit': 'metric tonne',
        'hot_dry': True,
        'coastal_humid': False,
        'heavy_rainfall': True,
        'cold_hilly': False,
        'cyclone_prone': False,
        'states_available': ['Andhra Pradesh', 'Telangana', 'Odisha', 'Tamil Nadu',
                             'Karnataka'],
        'seismic_zone': 'II',
        'specifications': {
            'IS Code': 'IS 1786:2008',
            'Grade': 'Fe 415',
            'Yield Strength': '415 MPa min',
            'UTS': '485 MPa min',
            'Elongation': '14.5% min',
        },
        'average_rating': 4.4,
        'total_reviews': 112,
    },

    # ═══════════════════════════════════════════
    # BRICK (5 products)
    # ═══════════════════════════════════════════

    {
        'name': 'Traditional Red Clay Brick (Class A)',
        'brand': 'Local Kilns',
        'manufacturer': 'Various Regional Manufacturers',
        'category': 'brick',
        'subcategory': 'Burnt Clay Brick',
        'is_code': 'IS 1077',
        'description': (
            'Traditional hand-moulded red clay bricks, kiln-fired to Class A standard. '
            'The most widely used brick in India for centuries. Excellent thermal mass '
            'keeps interiors cool in hot-dry climates. However, low water absorption '
            'resistance makes them unsuitable for high-rainfall or waterlogged areas '
            'without waterproof plastering. Locally sourced — supports regional economy '
            'and reduces transportation carbon footprint.'
        ),
        'price': 8,
        'mrp': 10,
        'unit': 'piece',
        'hot_dry': True,
        'coastal_humid': False,
        'heavy_rainfall': False,
        'cold_hilly': True,
        'cyclone_prone': False,
        'states_available': ['UP', 'Bihar', 'West Bengal', 'Odisha', 'Rajasthan',
                             'MP', 'Delhi NCR', 'Haryana', 'Punjab'],
        'seismic_zone': 'III',
        'regional_notes': 'Availability limited in coastal Kerala and Tamil Nadu where concrete blocks dominate.',
        'specifications': {
            'IS Code': 'IS 1077:1992',
            'Class': 'A',
            'Compressive Strength': '10 MPa min',
            'Water Absorption': '< 20% by weight',
            'Standard Size': '230 × 110 × 75 mm',
            'Efflorescence': 'Nil to slight',
        },
        'average_rating': 4.0,
        'total_reviews': 201,
    },

    {
        'name': 'Fly Ash Brick (Class C)',
        'brand': 'Eco Build Bricks',
        'manufacturer': 'Various Green Manufacturers',
        'category': 'brick',
        'subcategory': 'Fly Ash Brick',
        'is_code': 'IS 12894',
        'description': (
            'Fly ash bricks are manufactured from thermal power plant waste (fly ash) '
            'mixed with lime, gypsum, and sand. Superior water resistance compared to '
            'clay bricks — suitable for Kerala, coastal areas, and heavy-rainfall zones. '
            'Uniform size reduces mortar consumption. Lighter weight reduces dead load. '
            'Eco-friendly: recycles industrial waste and consumes no topsoil unlike '
            'clay bricks. BIS certified to IS 12894.'
        ),
        'price': 7,
        'mrp': 9,
        'unit': 'piece',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': False,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh',
                             'Maharashtra', 'Odisha', 'West Bengal', 'Delhi NCR'],
        'seismic_zone': 'III',
        'specifications': {
            'IS Code': 'IS 12894:2002',
            'Compressive Strength': '7.5 MPa min',
            'Water Absorption': '< 12% by weight',
            'Standard Size': '230 × 110 × 75 mm',
            'Fly Ash Content': '55–70%',
        },
        'average_rating': 4.3,
        'total_reviews': 167,
    },

    {
        'name': 'Siporex AAC Blocks (600×200×200mm)',
        'brand': 'Siporex',
        'manufacturer': 'Siporex India Pvt. Ltd.',
        'category': 'brick',
        'subcategory': 'AAC Blocks',
        'is_code': 'IS 2185 Part 3',
        'description': (
            'Autoclaved Aerated Concrete (AAC) blocks are lightweight, thermally '
            'insulating, and acoustically superior to clay bricks. Manufactured by '
            'aerating a slurry of cement, fly ash, lime, and aluminium powder, then '
            'autoclaving at high pressure. 3× larger than a standard brick = faster '
            'construction. Excellent thermal insulation reduces air conditioning costs. '
            'Fire-resistant. Recommended for all climates — especially hot-dry and '
            'coastal areas where energy efficiency matters most.'
        ),
        'price': 45,
        'mrp': 55,
        'unit': 'piece',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh',
                             'Maharashtra', 'Gujarat', 'Rajasthan', 'Delhi NCR', 'UP'],
        'seismic_zone': 'IV',
        'regional_notes': 'Thermal resistance (R-value) is especially valuable in Rajasthan and Gujarat summers.',
        'specifications': {
            'IS Code': 'IS 2185 (Part 3):1984',
            'Density': '550–650 kg/m³',
            'Compressive Strength': '3.5–4.0 MPa',
            'Thermal Conductivity': '0.16 W/mK',
            'Fire Resistance': '4 hours (250mm wall)',
            'Size': '600 × 200 × 200 mm',
            'Sound Reduction': '42 dB (200mm wall)',
        },
        'average_rating': 4.6,
        'total_reviews': 245,
    },

    {
        'name': 'Wienerberger Porotherm Clay Blocks',
        'brand': 'Wienerberger',
        'manufacturer': 'Wienerberger India Pvt. Ltd.',
        'category': 'brick',
        'subcategory': 'Hollow Clay Blocks',
        'is_code': 'IS 3952',
        'description': (
            'Porotherm hollow clay blocks combine traditional clay with modern precision '
            'manufacturing. The hollow core provides excellent thermal insulation while '
            'reducing dead weight by 30% vs solid brick. Mortar-free Porotherm Dryfix '
            'variant uses thin-layer adhesive, cutting construction time by 50%. '
            'Highly recommended for Kerala, Tamil Nadu, and Andhra Pradesh where '
            'humidity-controlled interiors are valued.'
        ),
        'price': 55,
        'mrp': 65,
        'unit': 'piece',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': False,
        'cyclone_prone': False,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh',
                             'Maharashtra', 'Gujarat', 'Delhi NCR'],
        'seismic_zone': 'III',
        'specifications': {
            'IS Code': 'IS 3952:1988',
            'Density': '800–900 kg/m³',
            'Compressive Strength': '3.5 MPa',
            'Thermal Conductivity': '0.19 W/mK',
            'Available Sizes': '400×200×200mm, 400×200×150mm, 400×200×100mm',
        },
        'average_rating': 4.5,
        'total_reviews': 118,
    },

    {
        'name': 'Solid Concrete Block (400×200×200mm)',
        'brand': 'Local Manufacturers',
        'manufacturer': 'Various Regional Precast Units',
        'category': 'brick',
        'subcategory': 'Concrete Block',
        'is_code': 'IS 2185 Part 1',
        'description': (
            'Dense solid concrete blocks made from cement, aggregate, and sand. '
            'Higher compressive strength than clay bricks. Low water absorption makes '
            'them suitable for Kerala and coastal regions. Locally manufactured — '
            'reduces material cost in areas where cement is readily available. '
            'Not thermally efficient (no insulation value) — compensate with wall '
            'cavity or insulation board in hot climates.'
        ),
        'price': 38,
        'mrp': 45,
        'unit': 'piece',
        'hot_dry': False,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh',
                             'Goa', 'Maharashtra'],
        'seismic_zone': 'III',
        'specifications': {
            'IS Code': 'IS 2185 (Part 1):2005',
            'Compressive Strength': '5 MPa min (Type B)',
            'Water Absorption': '10% max',
            'Size': '400 × 200 × 200 mm',
            'Density': '1800–2200 kg/m³',
        },
        'average_rating': 4.1,
        'total_reviews': 134,
    },

    # ═══════════════════════════════════════════
    # SAND & AGGREGATE (4 products)
    # ═══════════════════════════════════════════

    {
        'name': 'Natural River Sand (Zone II)',
        'brand': 'Licensed River Sand Suppliers',
        'manufacturer': 'Quarry / Mining Operations',
        'category': 'sand',
        'subcategory': 'Fine Aggregate',
        'is_code': 'IS 383',
        'description': (
            'Natural river sand — the traditional fine aggregate for concrete and '
            'mortar. Zone II gradation is ideal for most construction applications. '
            'High roundness of particles improves workability. However, over-exploitation '
            'of riverbeds has led to supply restrictions and price volatility across India. '
            'Ensure your supplier holds valid State Mining Lease permits. '
            'Consider M-Sand as a sustainable substitute in areas where it is available.'
        ),
        'price': 1800,
        'mrp': 2200,
        'unit': 'metric tonne',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh',
                             'Maharashtra', 'UP', 'Bihar', 'West Bengal'],
        'seismic_zone': None,
        'regional_notes': 'Check local State Sand Policy before purchase — river sand mining is regulated.',
        'specifications': {
            'IS Code': 'IS 383:2016',
            'Zone': 'Zone II',
            'Fineness Modulus': '2.6–2.9',
            'Silt Content': '< 3% by weight',
            'Organic Impurities': 'Nil',
            'Specific Gravity': '2.6–2.65',
        },
        'average_rating': 4.2,
        'total_reviews': 88,
    },

    {
        'name': 'M-Sand (Manufactured / Crushed Sand)',
        'brand': 'Blue Metal & M-Sand Industries',
        'manufacturer': 'Various Crusher Units',
        'category': 'sand',
        'subcategory': 'Fine Aggregate',
        'is_code': 'IS 383',
        'description': (
            'M-Sand (Manufactured Sand) is produced by crushing granite or basalt '
            'quarry stone to sand-size particles. Consistent grading, zero organic '
            'impurities, and controlled silt content make it a technically superior '
            'and more sustainable alternative to river sand. Increasingly mandatory '
            'in Kerala, Tamil Nadu, and Karnataka as natural sand becomes scarce. '
            'Slightly angular particles may require 10–15% more water for the same '
            'workability — adjust water-cement ratio accordingly.'
        ),
        'price': 1400,
        'mrp': 1700,
        'unit': 'metric tonne',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh',
                             'Maharashtra', 'Rajasthan', 'Gujarat'],
        'seismic_zone': None,
        'regional_notes': 'Mandated by Kerala and Tamil Nadu PWD for all government projects.',
        'specifications': {
            'IS Code': 'IS 383:2016',
            'Zone': 'Zone II / III',
            'Fineness Modulus': '2.5–3.0',
            'Silt Content': '< 2% by weight',
            'Specific Gravity': '2.6–2.7',
            'Source Material': 'Granite / Basalt',
        },
        'average_rating': 4.4,
        'total_reviews': 143,
    },

    {
        'name': '20mm Crushed Granite Aggregate',
        'brand': 'Blue Metal Crushers',
        'manufacturer': 'Various Quarry Operations',
        'category': 'aggregate',
        'subcategory': 'Coarse Aggregate',
        'is_code': 'IS 383',
        'description': (
            '20mm crushed granite is the standard coarse aggregate for all structural '
            'concrete. Granite aggregate produces high-strength concrete with excellent '
            'durability. The 20mm nominal size suits RCC slabs, beams, columns, and '
            'foundations. All-weather suitable — granite does not react with seawater '
            'or sulfates. Ensure aggregate is free from dust, clay coatings, and '
            'organic matter before use.'
        ),
        'price': 1600,
        'mrp': 1900,
        'unit': 'metric tonne',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh',
                             'Maharashtra', 'Rajasthan', 'Gujarat', 'Delhi NCR'],
        'seismic_zone': None,
        'specifications': {
            'IS Code': 'IS 383:2016',
            'Nominal Size': '20mm',
            'Los Angeles Abrasion Value': '< 30%',
            'Impact Value': '< 30%',
            'Water Absorption': '< 2%',
            'Specific Gravity': '2.6–2.7',
            'Flakiness Index': '< 35%',
        },
        'average_rating': 4.3,
        'total_reviews': 76,
    },

    {
        'name': '40mm Crushed Granite Aggregate',
        'brand': 'Blue Metal Crushers',
        'manufacturer': 'Various Quarry Operations',
        'category': 'aggregate',
        'subcategory': 'Coarse Aggregate',
        'is_code': 'IS 383',
        'description': (
            '40mm nominal-size aggregate for mass concrete applications — foundations, '
            'retaining walls, plinth filling, and road sub-base. Larger size reduces '
            'cement content per cubic metre of concrete, cutting cost for non-structural '
            'applications. Not suitable for slabs thinner than 150mm or columns narrower '
            'than 120mm where the maximum aggregate size would interfere with rebar cover.'
        ),
        'price': 1500,
        'mrp': 1800,
        'unit': 'metric tonne',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Maharashtra',
                             'Gujarat', 'Rajasthan'],
        'seismic_zone': None,
        'specifications': {
            'IS Code': 'IS 383:2016',
            'Nominal Size': '40mm',
            'Los Angeles Abrasion Value': '< 30%',
            'Water Absorption': '< 2%',
            'Specific Gravity': '2.6–2.7',
            'Typical Use': 'Mass concrete, foundations, road sub-base',
        },
        'average_rating': 4.1,
        'total_reviews': 54,
    },

    # ═══════════════════════════════════════════
    # TILE (5 products)
    # ═══════════════════════════════════════════

    {
        'name': 'Kajaria Vitrified Floor Tile (600×600mm)',
        'brand': 'Kajaria Ceramics',
        'manufacturer': 'Kajaria Ceramics Limited',
        'category': 'tile',
        'subcategory': 'Vitrified Tile',
        'is_code': 'IS 15622',
        'description': (
            'Kajaria is India\'s largest ceramic tile manufacturer. Full-body vitrified '
            'tiles have near-zero water absorption (<0.5%), making them ideal for '
            'Kerala, coastal homes, and any area with high humidity or water exposure. '
            'Scratch-resistant surface (Mohs 7+) outlasts marble and natural stone. '
            'Available in 200+ designs mimicking marble, wood, and cement looks. '
            'GreenPro certified — low VOC production.'
        ),
        'price': 62,
        'mrp': 75,
        'unit': 'sq ft',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh',
                             'Maharashtra', 'Gujarat', 'Rajasthan', 'Delhi NCR', 'UP'],
        'seismic_zone': None,
        'specifications': {
            'IS Code': 'IS 15622:2017',
            'Size': '600 × 600 mm',
            'Thickness': '9–10 mm',
            'Water Absorption': '< 0.5%',
            'Breaking Strength': '1300 N min',
            'Slip Resistance (PTV)': '36 (dry)',
            'Surface Finish': 'Polished / Matt / Rustic',
        },
        'average_rating': 4.5,
        'total_reviews': 287,
    },

    {
        'name': 'Somany Ceramic Wall Tile (300×450mm)',
        'brand': 'Somany Ceramics',
        'manufacturer': 'Somany Ceramics Limited',
        'category': 'tile',
        'subcategory': 'Ceramic Wall Tile',
        'is_code': 'IS 13630',
        'description': (
            'Somany ceramic wall tiles for bathrooms, kitchens, and feature walls. '
            'Higher water absorption (6–10%) than vitrified — suitable for walls '
            'only, not floors. Glossy glaze provides easy-clean surface resistant to '
            'staining and mould. Extensive colour palette with 150+ design options. '
            'Lighter weight than vitrified tiles reduces adhesive and structural load.'
        ),
        'price': 35,
        'mrp': 42,
        'unit': 'sq ft',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Maharashtra',
                             'Gujarat', 'Delhi NCR', 'UP', 'Rajasthan'],
        'seismic_zone': None,
        'specifications': {
            'IS Code': 'IS 13630:2006',
            'Size': '300 × 450 mm',
            'Thickness': '7–8 mm',
            'Water Absorption': '6–10%',
            'Use': 'Walls only — not suitable for floors',
            'Finish': 'Glossy / Satin',
        },
        'average_rating': 4.2,
        'total_reviews': 193,
    },

    {
        'name': 'Johnson Anti-Skid Parking Tile (600×600mm)',
        'brand': 'Johnson Tiles',
        'manufacturer': 'Prism Johnson Limited',
        'category': 'tile',
        'subcategory': 'Anti-Skid Tile',
        'is_code': 'IS 15622',
        'description': (
            'Heavy-duty vitrified tile with deep groove anti-skid surface for parking '
            'areas, driveways, terraces, and ramps. High load-bearing capacity. '
            'PTV (Pendulum Test Value) > 45 ensures pedestrian safety even when wet. '
            'Frost-resistant — suitable for Himalayan foothills and cold-hilly regions. '
            'Acid and alkali resistant for industrial environments.'
        ),
        'price': 55,
        'mrp': 68,
        'unit': 'sq ft',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Maharashtra',
                             'Gujarat', 'Delhi NCR', 'UP', 'HP', 'Uttarakhand'],
        'seismic_zone': None,
        'specifications': {
            'IS Code': 'IS 15622:2017',
            'Size': '600 × 600 mm',
            'Thickness': '10 mm',
            'Water Absorption': '< 0.5%',
            'Slip Resistance (PTV)': '> 45 (wet)',
            'Breaking Strength': '1800 N min',
            'Frost Resistance': 'Yes',
        },
        'average_rating': 4.6,
        'total_reviews': 142,
    },

    {
        'name': 'RAK Porcelain Tile (600×1200mm)',
        'brand': 'RAK Ceramics',
        'manufacturer': 'RAK Ceramics India Pvt. Ltd.',
        'category': 'tile',
        'subcategory': 'Porcelain Tile',
        'is_code': 'IS 15622',
        'description': (
            'RAK large-format porcelain slabs for luxury residential and commercial '
            'interiors. 600×1200mm size creates seamless, high-end look with fewer '
            'grout lines. Full-body porcelain with consistent colour throughout — '
            'chips blend in, unlike surface-glazed tiles. UV-resistant — no colour '
            'fade on sun-exposed terraces. Requires specialist tile adhesive and '
            'professional installation for large format.'
        ),
        'price': 95,
        'mrp': 115,
        'unit': 'sq ft',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Maharashtra',
                             'Gujarat', 'Delhi NCR', 'Andhra Pradesh'],
        'seismic_zone': None,
        'specifications': {
            'IS Code': 'IS 15622:2017',
            'Size': '600 × 1200 mm',
            'Thickness': '10–12 mm',
            'Water Absorption': '< 0.05%',
            'Breaking Strength': '2000 N min',
            'Surface': 'Matt / Satin / Polished',
        },
        'average_rating': 4.7,
        'total_reviews': 76,
    },

    {
        'name': 'Nitco Marbonite Marble-Look Vitrified Tile (800×800mm)',
        'brand': 'Nitco',
        'manufacturer': 'Nitco Limited',
        'category': 'tile',
        'subcategory': 'Vitrified Tile',
        'is_code': 'IS 15622',
        'description': (
            'Nitco Marbonite is a premium Italian-inspired vitrified tile that replicates '
            'natural marble\'s veining without its maintenance hassles. Unlike real marble, '
            'Marbonite does not absorb stains, acid etch, or require annual polishing. '
            'Water absorption < 0.1% makes it suitable for all Indian climates including '
            'humid coastal Kerala. The 800mm format creates a grand, large-room feel.'
        ),
        'price': 85,
        'mrp': 102,
        'unit': 'sq ft',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Maharashtra',
                             'Gujarat', 'Delhi NCR'],
        'seismic_zone': None,
        'specifications': {
            'IS Code': 'IS 15622:2017',
            'Size': '800 × 800 mm',
            'Thickness': '10 mm',
            'Water Absorption': '< 0.1%',
            'Breaking Strength': '1500 N min',
            'Finish': 'High-gloss polished',
        },
        'average_rating': 4.5,
        'total_reviews': 109,
    },

    # ═══════════════════════════════════════════
    # PAINT (3 products)
    # ═══════════════════════════════════════════

    {
        'name': 'Asian Paints Tractor Emulsion (Interior)',
        'brand': 'Asian Paints',
        'manufacturer': 'Asian Paints Limited',
        'category': 'paint',
        'subcategory': 'Interior Emulsion',
        'is_code': 'IS 15489',
        'description': (
            'Tractor Emulsion is India\'s most trusted economy interior wall paint. '
            'Smooth, washable finish that handles everyday stains. Low VOC formula '
            'safe for bedrooms and children\'s rooms. Excellent coverage (10–12 sq m '
            'per litre). Available in 1500+ shades via Asian Paints ColourNext system. '
            'For humid climates like Kerala, pair with Damp Shield primer beneath for '
            'mould prevention.'
        ),
        'price': 280,
        'mrp': 310,
        'unit': 'litre',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh',
                             'Maharashtra', 'Gujarat', 'Rajasthan', 'Delhi NCR', 'UP'],
        'seismic_zone': None,
        'specifications': {
            'IS Code': 'IS 15489:2004',
            'Type': 'Interior Acrylic Emulsion',
            'Coverage': '10–12 m² per litre (2 coats)',
            'Drying Time': '2 hours (surface), 4 hours (recoat)',
            'Finish': 'Matt',
            'VOC Content': 'Low (< 50 g/L)',
            'Dilution': 'Water-based',
        },
        'average_rating': 4.3,
        'total_reviews': 512,
    },

    {
        'name': 'Berger WeatherCoat All Guard (Exterior)',
        'brand': 'Berger Paints',
        'manufacturer': 'Berger Paints India Limited',
        'category': 'paint',
        'subcategory': 'Exterior Emulsion',
        'is_code': 'IS 15489',
        'description': (
            'Berger WeatherCoat All Guard is engineered specifically for India\'s '
            'extreme weather — UV radiation, monsoon rain, coastal humidity, and '
            'thermal cycling. Elastomeric film bridges hairline cracks up to 0.3mm. '
            'Anti-algae and anti-fungal additives prevent black streaks in humid '
            'Kerala, Goa, and Konkan coast. 7-year weather guarantee. '
            'Essential for any exterior surface within 5 km of the coast.'
        ),
        'price': 365,
        'mrp': 410,
        'unit': 'litre',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Goa',
                             'Maharashtra', 'West Bengal', 'Odisha', 'Delhi NCR'],
        'seismic_zone': None,
        'specifications': {
            'IS Code': 'IS 15489:2004',
            'Type': 'Exterior Elastomeric Emulsion',
            'Coverage': '8–10 m² per litre (2 coats)',
            'Drying Time': '3 hours (surface), 6 hours (recoat)',
            'Finish': 'Smooth Matt',
            'UV Protection': 'High',
            'Anti-algae': 'Yes',
            'Crack Bridging': '0.3 mm',
            'Weather Warranty': '7 years',
        },
        'average_rating': 4.6,
        'total_reviews': 298,
    },

    {
        'name': 'Nerolac Excel Total (Exterior)',
        'brand': 'Kansai Nerolac Paints',
        'manufacturer': 'Kansai Nerolac Paints Limited',
        'category': 'paint',
        'subcategory': 'Exterior Emulsion',
        'is_code': 'IS 15489',
        'description': (
            'Nerolac Excel Total is a premium exterior paint with 3-in-1 protection: '
            'waterproofing, anti-algae, and anti-bacterial. Its advanced colloidal '
            'silica technology makes the surface hydrophobic (water-beads off) while '
            'remaining breathable (trapped moisture can escape). Excellent for Kerala '
            'and all monsoon-heavy regions. Lead-free and heavy metal-free formula '
            'compliant with latest Indian and European standards.'
        ),
        'price': 340,
        'mrp': 385,
        'unit': 'litre',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Maharashtra',
                             'Gujarat', 'Delhi NCR', 'UP', 'West Bengal'],
        'seismic_zone': None,
        'specifications': {
            'IS Code': 'IS 15489:2004',
            'Type': 'Exterior Acrylic Emulsion',
            'Coverage': '9–11 m² per litre (2 coats)',
            'Drying Time': '2.5 hours (surface), 5 hours (recoat)',
            'Technology': 'Colloidal Silica Hydrophobic',
            'Anti-algae & Anti-bacterial': 'Yes',
            'Lead Free': 'Yes',
            'Weather Warranty': '6 years',
        },
        'average_rating': 4.4,
        'total_reviews': 187,
    },

    # ═══════════════════════════════════════════
    # WATERPROOFING (2 products)
    # ═══════════════════════════════════════════

    {
        'name': 'Dr. Fixit Powder Waterproof',
        'brand': 'Dr. Fixit (Pidilite)',
        'manufacturer': 'Pidilite Industries Limited',
        'category': 'waterproofing',
        'subcategory': 'Cementitious Waterproofing',
        'is_code': 'IS 2645',
        'description': (
            'Dr. Fixit Powder Waterproof is a crystalline waterproofing compound '
            'mixed directly into concrete at the batching stage. Unlike surface-applied '
            'membranes, it becomes an integral part of the concrete matrix — waterproofing '
            'cannot peel off, be punctured, or be damaged by construction traffic. '
            'Recommended for water tanks, swimming pools, basement walls, and flat roof '
            'slabs in all Indian climates. Used at 200g per 50kg cement bag.'
        ),
        'price': 75,
        'mrp': 90,
        'unit': 'kg',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': True,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh',
                             'Maharashtra', 'Gujarat', 'Rajasthan', 'Delhi NCR', 'UP'],
        'seismic_zone': None,
        'regional_notes': 'Essential for all flat-roof construction in Kerala\'s heavy rainfall zone.',
        'specifications': {
            'IS Code': 'IS 2645:2003',
            'Type': 'Crystalline / Integral Waterproofing',
            'Dosage': '200 g per 50 kg cement bag',
            'Application': 'Added to concrete mix water',
            'Water Resistance': 'Positive and negative side',
            'NSF/ANSI 61': 'Safe for drinking water contact',
        },
        'average_rating': 4.7,
        'total_reviews': 334,
    },

    {
        'name': 'STP Bituminous Waterproofing Membrane (4mm)',
        'brand': 'STP Limited',
        'manufacturer': 'STP Limited',
        'category': 'waterproofing',
        'subcategory': 'Bituminous Membrane',
        'is_code': 'IS 1322',
        'description': (
            'STP 4mm torch-on bituminous membrane for flat roofs, podium decks, '
            'and basement external walls. APP (Atactic Polypropylene) modified for '
            'superior heat and UV resistance — critical for hot-dry Rajasthan and '
            'Gujarat terraces. Torch-applied creates a seamless, fully bonded layer '
            'with no seams or joints for water to penetrate. 15-year expected service '
            'life. Not recommended for areas below -5°C (membrane becomes brittle).'
        ),
        'price': 145,
        'mrp': 170,
        'unit': 'sq ft',
        'hot_dry': True,
        'coastal_humid': True,
        'heavy_rainfall': True,
        'cold_hilly': False,
        'cyclone_prone': True,
        'states_available': ['Kerala', 'Tamil Nadu', 'Karnataka', 'Maharashtra',
                             'Gujarat', 'Rajasthan', 'Delhi NCR', 'UP', 'West Bengal'],
        'seismic_zone': None,
        'regional_notes': 'Not recommended above 2500m altitude or in regions with sub-zero winters.',
        'specifications': {
            'IS Code': 'IS 1322:1993',
            'Type': 'APP Modified Bituminous Membrane',
            'Thickness': '4 mm',
            'Application': 'Torch-on (hot applied)',
            'Service Temperature': '-10°C to +110°C',
            'Tensile Strength': '700 N/50mm',
            'Elongation': '30% min',
            'Expected Life': '15 years',
        },
        'average_rating': 4.4,
        'total_reviews': 91,
    },

]


# ─── Local static image mapping ─────────────────────────────────────────────────
# Images live in:  static/images/products/
# Django serves them at:  /static/images/products/<filename>
# Drop the image files into that folder — seed command wires them up automatically.
#
# 9 images cover all 30 products (category-based, with a few sub-variants):
#   cement.jpg         → OPC, PPC, PSC, SRC, OPC43 cement bags
#   white_cement.jpg   → Birla White Cement bag
#   steel.jpg          → all TMT bar products
#   brick.jpg          → red clay brick, fly ash brick, concrete block
#   aac.jpg            → Siporex AAC blocks, Wienerberger Porotherm
#   sand.jpg           → river sand, M-sand
#   aggregate.jpg      → 20mm and 40mm crushed granite
#   tile.jpg           → all vitrified, ceramic, porcelain tiles
#   paint.jpg          → all paint products
#   waterproofing.jpg  → Dr. Fixit, STP membrane

_BASE = '/static/images/products/'

# product name keyword  →  image filename
_NAME_IMAGE_MAP = [
    ('Birla White',      'white_cement.jpg'),
    ('AAC',              'aac.jpg'),
    ('Porotherm',        'aac.jpg'),
    ('Siporex',          'aac.jpg'),
    ('Wienerberger',     'aac.jpg'),
]

# category  →  image filename (fallback when no name match)
_CAT_IMAGE_MAP = {
    'cement':        'cement.jpg',
    'steel':         'steel.jpg',
    'brick':         'brick.jpg',
    'sand':          'sand.jpg',
    'aggregate':     'aggregate.jpg',
    'tile':          'tile.jpg',
    'paint':         'paint.jpg',
    'waterproofing': 'waterproofing.jpg',
}


def _image_path(name, category):
    """Return the local static URL for a product given its name and category."""
    for keyword, filename in _NAME_IMAGE_MAP:
        if keyword.lower() in name.lower():
            return _BASE + filename
    return _BASE + _CAT_IMAGE_MAP.get(category, 'cement.jpg')


class Command(BaseCommand):
    help = 'Seed the database with 30 construction material products for demo.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing products before seeding.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = Product.objects.count()
            Product.objects.all().delete()   # cascades to ProductImage rows
            self.stdout.write(self.style.WARNING(f'Cleared {count} existing products.'))

        created = 0
        skipped = 0

        for data in PRODUCTS:
            # slug will be auto-generated in Product.save() from the name
            # so we check by name to avoid duplicates on re-runs
            if Product.objects.filter(name=data['name']).exists():
                self.stdout.write(f'  SKIP  {data["name"][:60]}')
                skipped += 1
                continue

            product = Product.objects.create(**data)

            # Create one ProductImage record using local static file path
            image_url = _image_path(data['name'], data['category'])
            ProductImage.objects.create(
                product=product,
                image_url=image_url,
                caption=data['name'],
                is_primary=True,
                sort_order=0,
            )

            self.stdout.write(self.style.SUCCESS(
                f'  ADD   {data["name"][:55]}'
            ))
            created += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done. {created} products created, {skipped} skipped (already exist).'
        ))
        self.stdout.write('')
        self.stdout.write('DEMO FLOW CHECK:')
        opc = Product.objects.filter(name__icontains='OPC 53').first()
        ppc = Product.objects.filter(name__icontains='PPC').first()
        if opc:
            self.stdout.write(f'  OPC 53  coastal_humid={opc.coastal_humid}  '
                              f'(should be False — shows WARNING banner)')
        if ppc:
            self.stdout.write(f'  PPC     coastal_humid={ppc.coastal_humid}  '
                              f'(should be True  — shows as ALTERNATIVE)')
