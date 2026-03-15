"""
Management command: seed_providers

Creates realistic verified service providers (contractors, architects,
interior designers) for demo/development purposes.

Usage:
    python manage.py seed_providers          # creates providers
    python manage.py seed_providers --clear  # deletes existing seeded providers first
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.users.models import User, ServiceProviderProfile


PROVIDERS = [
    # ── Contractors ──────────────────────────────────────────────────────────
    {
        'user_type': 'contractor',
        'first_name': 'Rajesh',
        'last_name': 'Menon',
        'email': 'rajesh.menon@example.com',
        'username': 'rajesh_menon',
        'city': 'Thrissur',
        'district': 'Thrissur',
        'state': 'Kerala',
        'bio': 'Specializing in traditional Kerala-style homes and modern villas. '
               'Over 18 years of experience delivering projects on time and within budget.',
        'profile': {
            'business_name': 'Menon Constructions',
            'years_of_experience': 18,
            'total_projects_completed': 142,
            'typical_project_duration': '8–14 months',
            'specializations': ['residential', 'traditional', 'luxury'],
            'price_range_min': 1800,
            'price_range_max': 3500,
            'price_unit': 'per sqft',
            'office_address': 'MG Road, Thrissur, Kerala 680001',
            'website': '',
            'whatsapp_number': '+919876543210',
        },
    },
    {
        'user_type': 'contractor',
        'first_name': 'Suresh',
        'last_name': 'Kumar',
        'email': 'suresh.kumar@example.com',
        'username': 'suresh_kumar',
        'city': 'Kochi',
        'district': 'Ernakulam',
        'state': 'Kerala',
        'bio': 'Expert in coastal construction with deep knowledge of humidity-resistant '
               'materials. RERA-registered contractor with 12 years in Ernakulam district.',
        'profile': {
            'business_name': 'Kumar Coastal Builders',
            'years_of_experience': 12,
            'total_projects_completed': 87,
            'typical_project_duration': '6–10 months',
            'specializations': ['residential', 'commercial', 'eco_friendly'],
            'price_range_min': 1600,
            'price_range_max': 2800,
            'price_unit': 'per sqft',
            'office_address': 'Marine Drive, Kochi, Kerala 682031',
            'whatsapp_number': '+919876543211',
        },
    },
    {
        'user_type': 'contractor',
        'first_name': 'Priya',
        'last_name': 'Nair',
        'email': 'priya.nair@example.com',
        'username': 'priya_nair',
        'city': 'Kozhikode',
        'district': 'Kozhikode',
        'state': 'Kerala',
        'bio': 'Women-led construction firm specializing in affordable housing and '
               'renovation. ISO 9001 certified. Serving North Kerala since 2010.',
        'profile': {
            'business_name': 'Nair Build Works',
            'years_of_experience': 14,
            'total_projects_completed': 108,
            'typical_project_duration': '5–9 months',
            'specializations': ['residential', 'renovation', 'smart_home'],
            'price_range_min': 1400,
            'price_range_max': 2400,
            'price_unit': 'per sqft',
            'office_address': 'Calicut Beach Road, Kozhikode 673001',
            'whatsapp_number': '+919876543212',
        },
    },
    {
        'user_type': 'contractor',
        'first_name': 'Thomas',
        'last_name': 'George',
        'email': 'thomas.george@example.com',
        'username': 'thomas_george',
        'city': 'Thiruvananthapuram',
        'district': 'Thiruvananthapuram',
        'state': 'Kerala',
        'bio': 'Premium villa contractor with a focus on luxury finishes and smart home '
               'integration. Delivered 60+ villas across South Kerala.',
        'profile': {
            'business_name': 'George Premium Homes',
            'years_of_experience': 20,
            'total_projects_completed': 63,
            'typical_project_duration': '12–18 months',
            'specializations': ['luxury', 'smart_home', 'modern'],
            'price_range_min': 3500,
            'price_range_max': 6000,
            'price_unit': 'per sqft',
            'office_address': 'Kowdiar, Thiruvananthapuram 695003',
            'website': '',
            'whatsapp_number': '+919876543213',
        },
    },

    # ── Architects ───────────────────────────────────────────────────────────
    {
        'user_type': 'architect',
        'first_name': 'Anitha',
        'last_name': 'Krishnan',
        'email': 'anitha.krishnan@example.com',
        'username': 'anitha_krishnan',
        'city': 'Kochi',
        'district': 'Ernakulam',
        'state': 'Kerala',
        'bio': 'Council of Architecture registered. Blending contemporary design with '
               'Kerala vernacular architecture. 15 years in residential and hospitality projects.',
        'profile': {
            'business_name': 'Krishnan Design Studio',
            'years_of_experience': 15,
            'total_projects_completed': 56,
            'typical_project_duration': '3–6 months (design phase)',
            'specializations': ['residential', 'modern', 'landscape'],
            'price_range_min': 80,
            'price_range_max': 150,
            'price_unit': 'per sqft (design)',
            'office_address': 'Panampilly Nagar, Kochi 682036',
            'website': '',
            'whatsapp_number': '+919876543214',
        },
    },
    {
        'user_type': 'architect',
        'first_name': 'Vivek',
        'last_name': 'Pillai',
        'email': 'vivek.pillai@example.com',
        'username': 'vivek_pillai',
        'city': 'Thrissur',
        'district': 'Thrissur',
        'state': 'Kerala',
        'bio': 'Sustainable architecture practitioner. Designs maximise natural ventilation '
               'and passive cooling — ideal for Kerala\'s humid climate. IGBC Green Homes certified.',
        'profile': {
            'business_name': 'Pillai Sustainable Architects',
            'years_of_experience': 10,
            'total_projects_completed': 34,
            'typical_project_duration': '2–4 months (design phase)',
            'specializations': ['eco_friendly', 'residential', 'structural'],
            'price_range_min': 70,
            'price_range_max': 120,
            'price_unit': 'per sqft (design)',
            'office_address': 'Shakthan Thampuran Nagar, Thrissur 680001',
            'whatsapp_number': '+919876543215',
        },
    },
    {
        'user_type': 'architect',
        'first_name': 'Deepa',
        'last_name': 'Varma',
        'email': 'deepa.varma@example.com',
        'username': 'deepa_varma',
        'city': 'Kozhikode',
        'district': 'Kozhikode',
        'state': 'Kerala',
        'bio': 'Specializes in commercial and mixed-use developments. Urban planning background '
               'from SPA Delhi. 13 years of award-winning projects in North Kerala.',
        'profile': {
            'business_name': 'Varma Architecture Co.',
            'years_of_experience': 13,
            'total_projects_completed': 41,
            'typical_project_duration': '4–8 months (design phase)',
            'specializations': ['commercial', 'urban_planning', 'modern'],
            'price_range_min': 90,
            'price_range_max': 180,
            'price_unit': 'per sqft (design)',
            'office_address': 'SM Street, Kozhikode 673001',
            'whatsapp_number': '+919876543216',
        },
    },
    {
        'user_type': 'architect',
        'first_name': 'Arun',
        'last_name': 'Chandran',
        'email': 'arun.chandran@example.com',
        'username': 'arun_chandran',
        'city': 'Thiruvananthapuram',
        'district': 'Thiruvananthapuram',
        'state': 'Kerala',
        'bio': 'Heritage conservation specialist and modern residential architect. '
               'Documented 30+ traditional Kerala tharavadus and designed contemporary homes inspired by them.',
        'profile': {
            'business_name': 'Chandran Heritage Architects',
            'years_of_experience': 22,
            'total_projects_completed': 78,
            'typical_project_duration': '3–12 months',
            'specializations': ['traditional', 'residential', 'landscape'],
            'price_range_min': 100,
            'price_range_max': 200,
            'price_unit': 'per sqft (design)',
            'office_address': 'Vellayambalam, Thiruvananthapuram 695010',
            'website': '',
            'whatsapp_number': '+919876543217',
        },
    },

    # ── Interior Designers ───────────────────────────────────────────────────
    {
        'user_type': 'interior_designer',
        'first_name': 'Meera',
        'last_name': 'Suresh',
        'email': 'meera.suresh@example.com',
        'username': 'meera_suresh',
        'city': 'Kochi',
        'district': 'Ernakulam',
        'state': 'Kerala',
        'bio': 'Contemporary interiors with a warm Kerala touch. '
               'Specialises in open-plan living spaces and bespoke furniture. '
               'Featured in Architecture + Design magazine.',
        'profile': {
            'business_name': 'Meera Interiors Studio',
            'years_of_experience': 9,
            'total_projects_completed': 72,
            'typical_project_duration': '2–4 months',
            'specializations': ['contemporary', 'minimalist', 'residential'],
            'price_range_min': 600,
            'price_range_max': 1200,
            'price_unit': 'per sqft',
            'office_address': 'Kadavanthra, Kochi 682020',
            'website': '',
            'whatsapp_number': '+919876543218',
        },
    },
    {
        'user_type': 'interior_designer',
        'first_name': 'Rajan',
        'last_name': 'Iyer',
        'email': 'rajan.iyer@example.com',
        'username': 'rajan_iyer',
        'city': 'Thrissur',
        'district': 'Thrissur',
        'state': 'Kerala',
        'bio': 'Luxury interiors for high-end villas and apartments. '
               'Collaborates with European furniture brands and custom craftsmen in Kerala.',
        'profile': {
            'business_name': 'Iyer Luxury Interiors',
            'years_of_experience': 16,
            'total_projects_completed': 48,
            'typical_project_duration': '3–6 months',
            'specializations': ['luxury', 'classic', 'contemporary'],
            'price_range_min': 1500,
            'price_range_max': 4000,
            'price_unit': 'per sqft',
            'office_address': 'Round South, Thrissur 680001',
            'whatsapp_number': '+919876543219',
        },
    },
    {
        'user_type': 'interior_designer',
        'first_name': 'Nisha',
        'last_name': 'Balan',
        'email': 'nisha.balan@example.com',
        'username': 'nisha_balan',
        'city': 'Kozhikode',
        'district': 'Kozhikode',
        'state': 'Kerala',
        'bio': 'Eco-friendly interiors using natural materials — bamboo, cane, reclaimed wood. '
               'Every project is designed to be healthy for the family and the planet.',
        'profile': {
            'business_name': 'Green Space Interiors',
            'years_of_experience': 7,
            'total_projects_completed': 39,
            'typical_project_duration': '2–3 months',
            'specializations': ['sustainable', 'minimalist', 'residential'],
            'price_range_min': 500,
            'price_range_max': 900,
            'price_unit': 'per sqft',
            'office_address': 'Palayam, Kozhikode 673002',
            'whatsapp_number': '+919876543220',
        },
    },
    {
        'user_type': 'interior_designer',
        'first_name': 'Arjun',
        'last_name': 'Dev',
        'email': 'arjun.dev@example.com',
        'username': 'arjun_dev',
        'city': 'Thiruvananthapuram',
        'district': 'Thiruvananthapuram',
        'state': 'Kerala',
        'bio': 'Smart home integration specialist. Designs beautiful spaces that are '
               'also fully automated — lighting, climate, security, and entertainment.',
        'profile': {
            'business_name': 'SmartHome Design Co.',
            'years_of_experience': 11,
            'total_projects_completed': 55,
            'typical_project_duration': '3–5 months',
            'specializations': ['smart_home', 'contemporary', 'residential'],
            'price_range_min': 900,
            'price_range_max': 2200,
            'price_unit': 'per sqft',
            'office_address': 'Pattom, Thiruvananthapuram 695004',
            'website': '',
            'whatsapp_number': '+919876543221',
        },
    },
]


PROVIDERS += [
    # ── Additional Contractors ────────────────────────────────────────────────
    {
        'user_type': 'contractor',
        'first_name': 'Biju',
        'last_name': 'Mathew',
        'email': 'biju.mathew@example.com',
        'username': 'biju_mathew',
        'city': 'Kottayam',
        'district': 'Kottayam',
        'state': 'Kerala',
        'bio': 'Renovation and extension specialist with a deep understanding of ageing '
               'Kerala homes. Skilled in seamlessly blending new additions with existing '
               'traditional structures. 8 years of hands-on experience in Kottayam district.',
        'profile': {
            'business_name': 'Mathew Renovation Works',
            'years_of_experience': 8,
            'total_projects_completed': 45,
            'typical_project_duration': '3–6 months',
            'specializations': ['renovation', 'residential', 'interior_work'],
            'price_range_min': 1200,
            'price_range_max': 2000,
            'price_unit': 'per sqft',
            'office_address': 'Nagampadam, Kottayam 686001',
            'whatsapp_number': '+919876543230',
        },
    },
    {
        'user_type': 'contractor',
        'first_name': 'Anoop',
        'last_name': 'Krishnan',
        'email': 'anoop.krishnan@example.com',
        'username': 'anoop_krishnan',
        'city': 'Palakkad',
        'district': 'Palakkad',
        'state': 'Kerala',
        'bio': 'Third-generation builder specialising in traditional Tharavadu-style homes '
               'and eco-friendly constructions. Uses locally sourced laterite stone and '
               'reclaimed teak. IGBC certified. 17 years, 98 projects across Palakkad.',
        'profile': {
            'business_name': 'Krishnan Heritage Builders',
            'years_of_experience': 17,
            'total_projects_completed': 98,
            'typical_project_duration': '10–16 months',
            'specializations': ['traditional', 'eco_friendly', 'residential'],
            'price_range_min': 1700,
            'price_range_max': 3000,
            'price_unit': 'per sqft',
            'office_address': 'Victoria College Road, Palakkad 678001',
            'whatsapp_number': '+919876543231',
        },
    },
    {
        'user_type': 'contractor',
        'first_name': 'Sherin',
        'last_name': 'Jose',
        'email': 'sherin.jose@example.com',
        'username': 'sherin_jose',
        'city': 'Alappuzha',
        'district': 'Alappuzha',
        'state': 'Kerala',
        'bio': 'Expert in flood-resilient and coastal construction. All projects use '
               'corrosion-resistant materials (PSC/PPC cement, SS fixtures) approved '
               'for Kerala\'s backwater regions. RERA registered.',
        'profile': {
            'business_name': 'Jose Coastal Builders',
            'years_of_experience': 11,
            'total_projects_completed': 67,
            'typical_project_duration': '6–12 months',
            'specializations': ['residential', 'commercial', 'eco_friendly'],
            'price_range_min': 1500,
            'price_range_max': 2600,
            'price_unit': 'per sqft',
            'office_address': 'Mullackal, Alappuzha 688011',
            'whatsapp_number': '+919876543232',
        },
    },

    # ── Additional Architects ─────────────────────────────────────────────────
    {
        'user_type': 'architect',
        'first_name': 'Pradeep',
        'last_name': 'Nambiar',
        'email': 'pradeep.nambiar@example.com',
        'username': 'pradeep_nambiar',
        'city': 'Kannur',
        'district': 'Kannur',
        'state': 'Kerala',
        'bio': 'Council of Architecture registered. 19 years designing homes that honour '
               'Malabar\'s vernacular architecture while meeting modern needs. '
               'Documented winner of Kerala State Award for residential design.',
        'profile': {
            'business_name': 'Nambiar Architects',
            'years_of_experience': 19,
            'total_projects_completed': 61,
            'typical_project_duration': '4–7 months (design phase)',
            'specializations': ['residential', 'traditional', 'landscape'],
            'price_range_min': 85,
            'price_range_max': 160,
            'price_unit': 'per sqft (design)',
            'office_address': 'Fort Road, Kannur 670001',
            'whatsapp_number': '+919876543233',
        },
    },
    {
        'user_type': 'architect',
        'first_name': 'Sindhu',
        'last_name': 'Raj',
        'email': 'sindhu.raj@example.com',
        'username': 'sindhu_raj',
        'city': 'Kochi',
        'district': 'Ernakulam',
        'state': 'Kerala',
        'bio': 'Structural design and sustainability specialist. LEED AP certified. '
               'Designs buildings that maximise natural light, cross-ventilation, and '
               'rainwater harvesting — cutting energy bills by 30–40% for clients.',
        'profile': {
            'business_name': 'Raj Sustainable Designs',
            'years_of_experience': 8,
            'total_projects_completed': 22,
            'typical_project_duration': '2–4 months (design phase)',
            'specializations': ['structural', 'eco_friendly', 'residential'],
            'price_range_min': 75,
            'price_range_max': 130,
            'price_unit': 'per sqft (design)',
            'office_address': 'Vytilla, Kochi 682019',
            'whatsapp_number': '+919876543234',
        },
    },

    # ── Additional Interior Designers ─────────────────────────────────────────
    {
        'user_type': 'interior_designer',
        'first_name': 'Lekha',
        'last_name': 'Pillai',
        'email': 'lekha.pillai@example.com',
        'username': 'lekha_pillai',
        'city': 'Kochi',
        'district': 'Ernakulam',
        'state': 'Kerala',
        'bio': 'Classic Kerala interiors meet modern comfort. Works exclusively with '
               'natural materials — polished laterite, handmade Calicut tiles, '
               'antique teak. Every space tells a story of Kerala\'s rich heritage.',
        'profile': {
            'business_name': 'Pillai Classic Interiors',
            'years_of_experience': 6,
            'total_projects_completed': 28,
            'typical_project_duration': '2–3 months',
            'specializations': ['classic', 'residential', 'sustainable'],
            'price_range_min': 550,
            'price_range_max': 1000,
            'price_unit': 'per sqft',
            'office_address': 'MG Road, Kochi 682035',
            'whatsapp_number': '+919876543235',
        },
    },
    {
        'user_type': 'interior_designer',
        'first_name': 'Jithin',
        'last_name': 'Kumar',
        'email': 'jithin.kumar@example.com',
        'username': 'jithin_kumar',
        'city': 'Kottayam',
        'district': 'Kottayam',
        'state': 'Kerala',
        'bio': 'Minimalist spaces that breathe. Specialises in apartment and compact-home '
               'design using built-in storage to maximise usable space. 10 years, 44 projects '
               'across Kottayam and Ernakulam.',
        'profile': {
            'business_name': 'Space Studio by Jithin',
            'years_of_experience': 10,
            'total_projects_completed': 44,
            'typical_project_duration': '2–4 months',
            'specializations': ['minimalist', 'sustainable', 'contemporary'],
            'price_range_min': 480,
            'price_range_max': 850,
            'price_unit': 'per sqft',
            'office_address': 'Baker Junction, Kottayam 686001',
            'whatsapp_number': '+919876543236',
        },
    },
    {
        'user_type': 'interior_designer',
        'first_name': 'Divya',
        'last_name': 'Menon',
        'email': 'divya.menon@example.com',
        'username': 'divya_menon',
        'city': 'Thiruvananthapuram',
        'district': 'Thiruvananthapuram',
        'state': 'Kerala',
        'bio': 'Contemporary interiors for discerning clients. Collaborates with '
               'Kerala craftsmen and European suppliers to create spaces that are '
               'both globally inspired and locally rooted.',
        'profile': {
            'business_name': 'Menon Design House',
            'years_of_experience': 13,
            'total_projects_completed': 58,
            'typical_project_duration': '3–5 months',
            'specializations': ['contemporary', 'luxury', 'residential'],
            'price_range_min': 800,
            'price_range_max': 1800,
            'price_unit': 'per sqft',
            'office_address': 'Statue Junction, Thiruvananthapuram 695001',
            'whatsapp_number': '+919876543237',
        },
    },
]


class Command(BaseCommand):
    help = 'Seed verified service providers (contractors, architects, designers) for demo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all seeded provider accounts before re-seeding',
        )

    def handle(self, *args, **options):
        seeded_emails = [p['email'] for p in PROVIDERS]

        if options['clear']:
            deleted, _ = User.objects.filter(email__in=seeded_emails).delete()
            self.stdout.write(self.style.WARNING(f'Cleared {deleted} seeded provider accounts.'))

        created_count = 0
        skipped_count = 0

        for data in PROVIDERS:
            email = data['email']

            if User.objects.filter(email=email).exists():
                skipped_count += 1
                continue

            # Create the user
            user = User.objects.create_user(
                username=data['username'],
                email=email,
                password='DemoPass@2026',   # demo password — change in production
                first_name=data['first_name'],
                last_name=data['last_name'],
                user_type=data['user_type'],
                city=data.get('city', ''),
                district=data.get('district', ''),
                state=data.get('state', 'Kerala'),
                bio=data.get('bio', ''),
                is_active=True,
            )

            # Create the approved service provider profile
            profile_data = data['profile']
            ServiceProviderProfile.objects.create(
                user=user,
                business_name=profile_data['business_name'],
                years_of_experience=profile_data['years_of_experience'],
                total_projects_completed=profile_data['total_projects_completed'],
                typical_project_duration=profile_data.get('typical_project_duration', ''),
                specializations=profile_data.get('specializations', []),
                price_range_min=profile_data.get('price_range_min'),
                price_range_max=profile_data.get('price_range_max'),
                price_unit=profile_data.get('price_unit', 'per sqft'),
                office_address=profile_data.get('office_address', ''),
                website=profile_data.get('website', ''),
                whatsapp_number=profile_data.get('whatsapp_number', ''),
                verification_status='approved',
                verified_at=timezone.now(),
            )

            created_count += 1
            self.stdout.write(
                f"  OK {profile_data['business_name']} ({data['user_type']}, {data['city']})"
            )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone — {created_count} providers created, {skipped_count} already existed.'
        ))
        self.stdout.write('  Login password for all seeded providers: DemoPass@2026')
