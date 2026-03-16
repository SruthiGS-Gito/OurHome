"""
apps/products/views.py — Views for the materials catalog.

THE DEMO FLOW THIS ENABLES:
1. User visits /materials/?climate=coastal_humid
2. Sees product cards with ✓/✗ climate badges
3. Clicks OPC 53 → /materials/ultratech-opc-53-cement/?from_climate=coastal_humid
4. Sees BIG WARNING: "Not recommended for Coastal regions"
5. Sees alternatives (PPC cement, etc.) that ARE coastal-suitable
6. Clicks PPC → sees GREEN: "Suitable for Coastal regions"

2 clicks. Maximum impact.
"""

import base64
import json
import uuid
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse, HttpResponseNotAllowed
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_POST

PRICE_STALE_DAYS = 90

from .models import Product, ViewHistory, SavedMaterial
from apps.reviews.models import Review
from apps.users.models import User, ServiceProviderProfile


# Human-readable labels for specialization codes stored in the DB.
_SPEC_LABELS = dict(ServiceProviderProfile.SPECIALIZATION_CHOICES)


# ──────────────────────────────────────────────────────────────
# Anthropic / AI Bill Analyzer constants
# ──────────────────────────────────────────────────────────────
_ANTHROPIC_SYSTEM = """You are OurHome's AI Material Advisor — an expert, honest assistant \
specialised in Kerala's construction industry.

Your purpose: Help homeowners in Kerala analyse contractor quotes/bills, understand material \
prices, check climate suitability, and make smart decisions.

Kerala market prices (2025, ±15% by district):
• OPC 53 Cement: ₹390–440 / 50 kg bag  • PPC Cement: ₹360–410 / 50 kg bag
• TMT Steel Fe500D: ₹58,000–68,000 / tonne  • AAC Blocks: ₹3,800–5,000 / cu.m
• Wire-cut Bricks: ₹7,000–11,000 / 1,000 bricks  • River Sand: ₹1,800–3,000 / tonne
• M-Sand: ₹800–1,400 / tonne  • Blue Metal 20mm: ₹1,200–1,900 / tonne
• Vitrified Tiles 600×600: ₹40–120 / sq.ft  • Exterior Emulsion: ₹250–420 / litre
• Interior Emulsion: ₹180–320 / litre  • Waterproofing Compound: ₹180–300 / kg

Climate rules:
• Coastal zones (Kochi, Kozhikode, Alappuzha): Use PPC/PSC cement NOT OPC; stainless \
fixtures; anti-corrosion exterior paint; AAC blocks preferred.
• Heavy rainfall (Wayanad, Idukki, Munnar): Waterproofing membrane essential; sloped roofs.
• All Kerala: Anti-fungal/moisture-resistant paint indoors; waterproofing admixture in concrete.

Rules for your responses:
• Be DIRECT and HONEST. Quantify every issue: "₹X per unit × Y units = ₹Z overcharge."
• For EVERY problem found (overpricing, wrong material, arithmetic error), give a concrete \
SOLUTION or ALTERNATIVE — never flag without guiding.
• If the quote is fair, say so clearly and reassuringly.
• Use markdown — the interface renders it.
• When uncertain about a price, say so honestly rather than guessing."""

_BILL_INITIAL_PROMPT = """Please analyse this contractor quote/bill carefully and completely.

## Overall Verdict
One clear sentence: is this quote fair, overpriced, or does it contain serious problems?

## Items Found
List every line item exactly as written in the bill.

## Price Analysis
For each item state: Kerala market rate · verdict (✅ FAIR / ⚠️ HIGH / 🚫 ABOVE MRP) · \
exact saving or overcharge amount.

## Climate Suitability
Which materials are unsuitable for Kerala's climate? For each, suggest a better alternative \
with its typical price.

## Arithmetic Check
Verify all calculations. Flag any errors with the correct figures.

## Solutions & Recommendations
For EVERY issue found, give a specific solution, alternative product or price to negotiate. \
Explain the impact.

## Final Summary
- Total quoted: ₹X
- Fair market total: ₹Y
- Potential savings: ₹Z
- Top 3 action items

Format rules:
- Use ✅ for FAIR, ⚠️ for HIGH, 🚫 for ILLEGAL/AVOID
- Keep each item to ONE line maximum
- Be concise — homeowners need quick decisions, not essays
- For every ⚠️ HIGH item, add one line: 💡 Switch to: [alternative] at ₹X"""


# Maps URL query param values → human-readable labels.
# Keys MUST exactly match the BooleanField names on the Product model.
CLIMATE_FILTERS = {
    'hot_dry':        'Hot & Dry',
    'coastal_humid':  'Coastal & Humid',
    'heavy_rainfall': 'Heavy Rainfall',
    'cold_hilly':     'Cold & Hilly',
    'cyclone_prone':  'Cyclone-Prone Coast',
}


# Extra metadata for the climate selector on the home page.
# emoji and regions are display-only — not stored on the model.
_CLIMATE_META = {
    'hot_dry':        ('☀️',  'Rajasthan, Gujarat, Tamil Nadu interior'),
    'coastal_humid':  ('🌊',  'Kerala, Goa, Konkan coast, Tamil Nadu coast'),
    'heavy_rainfall': ('🌧️', 'Northeast India, Western Ghats, Assam'),
    'cold_hilly':     ('❄️',  'Himachal Pradesh, Uttarakhand, J&K, Sikkim'),
    'cyclone_prone':  ('🌀',  'Odisha, Andhra Pradesh, Tamil Nadu coast'),
}


def home_view(request):
    """
    URL: /   (replaces the bare TemplateView)
    Template: templates/home.html

    Passes:
      featured_products — 4 most-reviewed active products (variety across categories)
      climate_cards     — list of dicts for the climate selector section
    """
    # 4 most-reviewed products as "Popular Materials"
    featured_products = (
        Product.objects
        .filter(is_active=True)
        .order_by('-total_reviews')[:4]
    )

    # Climate selector: one card per climate zone with live product count
    climate_cards = []
    for key, label in CLIMATE_FILTERS.items():
        emoji, regions = _CLIMATE_META[key]
        count = Product.objects.filter(is_active=True, **{key: True}).count()
        climate_cards.append({
            'key':     key,
            'label':   label,
            'emoji':   emoji,
            'regions': regions,
            'count':   count,
        })

    # Top 4 contractors and designers for the home page showcase
    def _featured_providers(user_type, url_type, count=4):
        type_filter = (
            {'user_type__in': user_type}
            if isinstance(user_type, (list, tuple))
            else {'user_type': user_type}
        )
        qs = (
            User.objects
            .filter(
                **type_filter,
                service_provider_profile__verification_status__in=['approved', 'pending'],
            )
            .select_related('service_provider_profile')
            .order_by('-service_provider_profile__total_projects_completed')[:count]
        )
        result = []
        for p in qs:
            prof = p.service_provider_profile
            spec_labels = [
                _SPEC_LABELS.get(s, s.replace('_', ' ').title())
                for s in (prof.specializations or [])[:2]
            ]
            result.append({
                'user': p,
                'profile': prof,
                'spec_labels': spec_labels,
                'url_type': url_type,
            })
        return result

    featured_contractors = _featured_providers('contractor', 'contractor_profile')
    featured_designers   = _featured_providers(['interior_designer', 'architect'], 'designer_profile')

    return render(request, 'home.html', {
        'featured_products':    featured_products,
        'climate_cards':        climate_cards,
        'featured_contractors': featured_contractors,
        'featured_designers':   featured_designers,
    })


@login_required
def product_list_view(request):
    """
    URL: /materials/
    Template: templates/products/product_list.html

    Supports two filter params (optional, combinable):
        ?category=cement
        ?climate=coastal_humid
        ?category=cement&climate=coastal_humid
    """
    products = Product.objects.filter(is_active=True)

    active_category = request.GET.get('category', '').strip()
    active_climate  = request.GET.get('climate', '').strip()
    active_sort     = request.GET.get('sort', 'popular').strip()
    active_phase    = request.GET.get('phase', '').strip()

    # SECURITY: Validate against allowlists before using as filter kwargs.
    # Prevents query manipulation even though Django ORM parameterizes SQL.
    valid_categories = [code for code, label in Product.CATEGORY_CHOICES]
    if active_category and active_category in valid_categories:
        products = products.filter(category=active_category)
    else:
        active_category = ''

    valid_phases = [code for code, label in Product.PHASE_CHOICES]
    if active_phase and active_phase in valid_phases:
        products = products.filter(phase=active_phase)
    else:
        active_phase = ''

    if active_climate and active_climate in CLIMATE_FILTERS:
        # **{active_climate: True} unpacks to e.g. filter(coastal_humid=True)
        products = products.filter(**{active_climate: True})
    else:
        active_climate = ''

    # IS Standard filter
    active_is_standard = request.GET.get('is_standard', '') == 'yes'
    if active_is_standard:
        products = products.filter(is_code__isnull=False).exclude(is_code='')

    SORT_OPTIONS = [
        ('popular',    'Most Popular'),
        ('price_asc',  'Price: Low to High'),
        ('price_desc', 'Price: High to Low'),
        ('top_rated',  'Top Rated'),
        ('newest',     'Newest First'),
    ]
    valid_sorts = [code for code, _ in SORT_OPTIONS]
    if active_sort not in valid_sorts:
        active_sort = 'popular'

    if active_sort == 'popular':
        products = products.order_by('-total_reviews', '-average_rating', 'name')
    elif active_sort == 'price_asc':
        products = products.order_by('price', 'name')
    elif active_sort == 'price_desc':
        products = products.order_by('-price', 'name')
    elif active_sort == 'top_rated':
        products = products.order_by('-average_rating', '-total_reviews', 'name')
    elif active_sort == 'newest':
        products = products.order_by('-created_at', 'name')

    # Count non-default active filters for the "Clear all (N)" badge
    active_filters_count = sum([
        bool(active_category),
        bool(active_climate),
        bool(active_phase),
        bool(active_is_standard),
        active_sort != 'popular',
    ])

    # Paginator(queryset, per_page) splits results into pages of 20.
    # .get_page() handles invalid/missing page numbers gracefully (no crash).
    paginator = Paginator(products, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj':              page_obj,
        'total_count':           paginator.count,
        'category_choices':      Product.CATEGORY_CHOICES,
        'phase_choices':         Product.PHASE_CHOICES,
        'climate_filters':       CLIMATE_FILTERS.items(),
        'active_category':       active_category,
        'active_climate':        active_climate,
        'active_climate_label':  CLIMATE_FILTERS.get(active_climate, ''),
        'active_sort':           active_sort,
        'active_phase':          active_phase,
        'active_is_standard':    active_is_standard,
        'active_filters_count':  active_filters_count,
    }
    return render(request, 'products/product_list.html', context)


@login_required
def product_detail_view(request, slug):
    """
    URL: /materials/<slug>/
    Template: templates/products/product_detail.html

    The from_climate parameter drives the demo's killer moment:
    When user comes from a climate-filtered list, we know what climate
    they care about and can immediately show whether this product is safe.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)

    from_climate          = request.GET.get('from_climate', '').strip()
    from_climate_label    = ''
    from_climate_suitable = None   # None = no filter active; False/True = filter active
    show_climate_warning  = False
    show_climate_success  = False
    climate_alternatives  = []

    if from_climate and from_climate in CLIMATE_FILTERS:
        from_climate_label = CLIMATE_FILTERS[from_climate]

        # getattr(product, 'coastal_humid') == product.coastal_humid
        # Works when field name is in a variable — same as attribute access, no security risk.
        from_climate_suitable = getattr(product, from_climate, False)

        if from_climate_suitable:
            show_climate_success = True
        else:
            show_climate_warning = True
            # Find alternatives: same category, IS suitable for this climate.
            # Order by actual approved review count (desc) so products with
            # real reviews — like PPC with its demo reviews — appear first.
            # Tiebreak by average_rating.
            climate_alternatives = (
                Product.objects
                .filter(category=product.category, is_active=True, **{from_climate: True})
                .exclude(pk=product.pk)
                .annotate(approved_reviews=Count('reviews', filter=Q(reviews__is_approved=True)))
                .order_by('-approved_reviews', '-average_rating')
            )[:3]

    # Track view history for logged-in users (update_or_create = no duplicates)
    if request.user.is_authenticated:
        ViewHistory.objects.update_or_create(
            user=request.user,
            product=product,
            defaults={'viewed_at': timezone.now()},
        )

    related_products = Product.objects.filter(
        category=product.category,
        is_active=True,
    ).exclude(pk=product.pk)[:4]

    # Approved reviews, most-helpful first
    reviews = Review.objects.filter(
        product=product, is_approved=True
    ).order_by('-helpful_count', '-created_at')

    # Pre-compute rating histogram bars for the template.
    # The template cannot call dict.get() with a loop variable, so we
    # build a plain list of dicts here and pass it as context.
    rating_bars = []
    for star in [5, 4, 3, 2, 1]:
        count = product.rating_breakdown.get(str(star), 0) if product.rating_breakdown else 0
        pct = round((count / product.total_reviews) * 100) if product.total_reviews > 0 else 0
        rating_bars.append({'star': star, 'count': count, 'pct': pct})

    is_saved = (
        request.user.is_authenticated and
        SavedMaterial.objects.filter(user=request.user, product=product).exists()
    )

    user_has_reviewed = (
        request.user.is_authenticated and
        Review.objects.filter(product=product, user=request.user).exists()
    )

    context = {
        'product':               product,
        'related_products':      related_products,
        'from_climate':          from_climate,
        'from_climate_label':    from_climate_label,
        'from_climate_suitable': from_climate_suitable,
        'show_climate_warning':  show_climate_warning,
        'show_climate_success':  show_climate_success,
        'climate_alternatives':  climate_alternatives,
        'reviews':               reviews,
        'rating_bars':           rating_bars,
        'is_saved':              is_saved,
        'user_has_reviewed':     user_has_reviewed,
    }
    return render(request, 'products/product_detail.html', context)


@login_required
@require_POST
def submit_review(request, slug):
    """
    POST /materials/<slug>/review/
    Creates a pending review for the product. Admin must approve before it shows.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)

    # Prevent duplicate reviews from the same user
    if Review.objects.filter(product=product, user=request.user).exists():
        from django.contrib import messages
        messages.warning(request, 'You have already submitted a review for this product.')
        return redirect('product_detail', slug=slug)

    rating  = request.POST.get('rating', '').strip()
    title   = request.POST.get('title', '').strip()
    comment = request.POST.get('comment', '').strip()

    # Validate required fields
    if not rating or not title or not comment:
        from django.contrib import messages
        messages.error(request, 'Please fill in all required fields (rating, title, and review).')
        return redirect('product_detail', slug=slug)

    try:
        rating_int = int(rating)
        if not 1 <= rating_int <= 5:
            raise ValueError
    except ValueError:
        from django.contrib import messages
        messages.error(request, 'Invalid rating — please select 1–5 stars.')
        return redirect('product_detail', slug=slug)

    Review.objects.create(
        product=product,
        user=request.user,
        rating=rating_int,
        title=title,
        review_text=comment,
        reviewer_name=request.user.full_name or request.user.username,
        reviewer_city=request.user.city or '',
        reviewer_state=request.user.state or '',
        reviewer_type=_reviewer_type_for(request.user),
        climate_type=request.POST.get('climate_type', ''),
        use_case=request.POST.get('use_case', ''),
        is_approved=False,    # Auto-approved for demo purposes
    )

    from django.contrib import messages
    messages.success(
        request,
        'Thanks for your review! It will appear once approved by our team (usually within 24 hours).'
    )
    return redirect('product_detail', slug=slug)


def _reviewer_type_for(user):
    """Maps user_type to Review.reviewer_type code."""
    return {
        'contractor':        'contractor',
        'architect':         'architect',
        'interior_designer': 'designer',
    }.get(user.user_type, 'homeowner')


@login_required
def bill_upload_view(request):
    """POST /material-analyzer/bill/ — upload PDF/image, run initial AI analysis."""
    if request.method != 'POST':
        return redirect('material_analyzer')

    uploaded = request.FILES.get('bill_file')
    if not uploaded:
        request.session['bill_error'] = 'Please select a file to upload.'
        return redirect('material_analyzer')

    allowed_types = {'image/jpeg', 'image/png', 'image/webp', 'application/pdf'}
    if uploaded.content_type not in allowed_types:
        request.session['bill_error'] = 'Only JPG, PNG, WEBP or PDF files are accepted.'
        return redirect('material_analyzer')

    if uploaded.size > 8 * 1024 * 1024:
        request.session['bill_error'] = 'File too large — maximum 8 MB.'
        return redirect('material_analyzer')

    if not getattr(settings, 'GROQ_API_KEY', ''):
        request.session['bill_error'] = 'AI analysis is not configured. Please add your GROQ_API_KEY to .env'
        return redirect('material_analyzer')

    file_data = uploaded.read()
    media_type = uploaded.content_type

    # Save to media/temp_bills/ so chat requests can re-read it
    temp_dir = Path(settings.MEDIA_ROOT) / 'temp_bills'
    temp_dir.mkdir(parents=True, exist_ok=True)
    ext = 'pdf' if 'pdf' in media_type else uploaded.name.rsplit('.', 1)[-1].lower()
    temp_path = temp_dir / f"{uuid.uuid4()}.{ext}"
    temp_path.write_bytes(file_data)

    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _ANTHROPIC_SYSTEM},
                {"role": "user", "content": _BILL_INITIAL_PROMPT},
            ],
            max_tokens=3000,
        )
        analysis = resp.choices[0].message.content
    except Exception as exc:
        temp_path.unlink(missing_ok=True)
        request.session['bill_error'] = f"AI analysis failed: {exc}"
        return redirect('material_analyzer')

    # Store in session: file path (for chat) + analysis text + history seed
    request.session['bill_temp_path']  = str(temp_path)
    request.session['bill_media_type'] = media_type
    request.session['bill_filename']   = uploaded.name
    request.session['bill_analysis']   = analysis
    # text-only history seed used by JS to initialise chatHistory
    request.session['bill_history_seed'] = json.dumps([
        {"role": "user",      "text": _BILL_INITIAL_PROMPT},
        {"role": "assistant", "text": analysis},
    ])
    request.session.modified = True
    return redirect('material_analyzer')


@login_required
def bill_chat_view(request):
    """POST /material-analyzer/chat/ — streaming SSE chat response."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    user_message   = (data.get('message') or '').strip()
    client_history = data.get('history') or []   # [{role, text}] from JS

    if not user_message:
        return JsonResponse({'error': 'Empty message'}, status=400)

    bill_temp_path = request.session.get('bill_temp_path', '')
    bill_media_type = request.session.get('bill_media_type', '')

    if not bill_temp_path:
        return JsonResponse({'error': 'No bill found. Please upload your bill first.'}, status=400)

    bill_path = Path(bill_temp_path)
    if not bill_path.exists():
        return JsonResponse({'error': 'Bill file expired. Please re-upload.'}, status=400)

    file_b64 = base64.standard_b64encode(bill_path.read_bytes()).decode()

    # Build conversation history; the file is attached inline to the first user turn
    full_history = list(client_history) + [{"role": "user", "text": user_message}]

    def _stream():
        full_text = ''
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)

            # Convert history to Groq's OpenAI-compatible messages format
            messages = [{"role": "system", "content": _ANTHROPIC_SYSTEM}]
            for msg in full_history:
                role = 'user' if msg['role'] == 'user' else 'assistant'
                messages.append({"role": role, "content": msg['text']})

            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=2000,
                stream=True,
            )
            for chunk in stream:
                text = chunk.choices[0].delta.content or ''
                if text:
                    full_text += text
                    yield f"data: {json.dumps(text)}\n\n"
            yield f"data: {json.dumps({'__done__': full_text})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'__error__': str(exc)})}\n\n"

    resp = StreamingHttpResponse(_stream(), content_type='text/event-stream')
    resp['Cache-Control'] = 'no-cache'
    resp['X-Accel-Buffering'] = 'no'
    return resp


@login_required
def bill_clear_view(request):
    """POST /material-analyzer/clear/ — clears active AI analysis from session."""
    if request.method == 'POST':
        temp_path = request.session.get('bill_temp_path', '')
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
        for key in ('bill_temp_path', 'bill_media_type', 'bill_filename',
                    'bill_analysis', 'bill_history_seed', 'bill_error'):
            request.session.pop(key, None)
        request.session.modified = True
    return redirect('material_analyzer')


@login_required
def material_analyzer_view(request):
    """
    URL: /material-analyzer/
    Template: templates/products/analyzer.html

    Quote Verifier — lets a homeowner paste in their contractor's material
    list and instantly see:
      1. Climate suitability per item (suitable / not suitable for chosen zone)
      2. Price verdict per item     (Fair / High / ILLEGAL — above MRP)
      3. Total quoted cost vs fair market cost

    No database writes. Everything is computed in memory per request.
    """
    products_qs = Product.objects.filter(is_active=True).order_by('category', 'name')

    report           = None
    selected_climate = ''
    error            = ''

    if request.method == 'POST':
        selected_climate = request.POST.get('climate', '').strip()
        product_ids      = request.POST.getlist('product_id')
        quoted_prices    = request.POST.getlist('quoted_price')
        quantities       = request.POST.getlist('quantity')

        # --- basic validation ---
        if not selected_climate or selected_climate not in CLIMATE_FILTERS:
            error = 'Please select a valid climate zone.'
        elif not any(pid.strip() for pid in product_ids):
            error = 'Please add at least one material to analyze.'
        else:
            items        = []
            total_quoted = Decimal('0')
            total_fair   = Decimal('0')
            parse_error  = False

            for pid, qp_raw, qty_raw in zip(product_ids, quoted_prices, quantities):
                pid     = pid.strip()
                qp_raw  = qp_raw.strip()
                qty_raw = qty_raw.strip()
                if not pid:
                    continue  # skip blank rows added but left empty

                try:
                    product      = Product.objects.get(pk=int(pid), is_active=True)
                    quoted_price = Decimal(qp_raw)
                    quantity     = Decimal(qty_raw)
                except (Product.DoesNotExist, ValueError, InvalidOperation):
                    parse_error = True
                    break

                if quoted_price <= 0 or quantity <= 0:
                    parse_error = True
                    break

                # --- climate suitability ---
                is_suitable = bool(getattr(product, selected_climate, False))

                # --- price verdict ---
                if quoted_price > product.mrp:
                    price_verdict = 'illegal'   # contractor quoting above legal MRP ceiling
                elif quoted_price > product.price:
                    price_verdict = 'high'      # above typical market, but below MRP
                else:
                    price_verdict = 'fair'      # at or below typical market price

                line_quoted = quoted_price * quantity
                line_fair   = product.price * quantity
                overcharge  = line_quoted - line_fair   # positive = overpaying, negative = savings

                total_quoted += line_quoted
                total_fair   += line_fair

                # --- price staleness ---
                if product.price_updated_at is None:
                    price_staleness = 'unknown'
                elif (timezone.now() - product.price_updated_at).days > PRICE_STALE_DAYS:
                    price_staleness = 'stale'
                else:
                    price_staleness = 'fresh'

                # --- price source badge info ---
                src = product.price_source
                conf = product.price_confidence
                if src == 'pwd_sor':
                    price_source_badge = {
                        'text': 'Kerala PWD SOR 2024 — Government verified rate',
                        'style': 'good',
                        'icon': '✓',
                    }
                elif src == 'ai_estimate' and conf == 'high':
                    price_source_badge = {
                        'text': 'AI Estimate (high confidence) — Verify with supplier',
                        'style': 'warn',
                        'icon': '~',
                    }
                elif src == 'ai_estimate':
                    price_source_badge = {
                        'text': f'AI Estimate ({conf} confidence) — Always verify before use',
                        'style': 'amber',
                        'icon': '⚠',
                    }
                else:
                    price_source_badge = {
                        'text': 'Baseline price — Not verified, for reference only',
                        'style': 'danger',
                        'icon': '⚠',
                    }

                # --- find alternatives for any problematic item ---
                alternatives = []
                if not is_suitable and selected_climate:
                    # Same category, suitable for this climate, best rated first
                    alternatives = list(
                        Product.objects.filter(
                            category=product.category, is_active=True,
                            **{selected_climate: True}
                        ).exclude(pk=product.pk)
                        .order_by('-average_rating')[:2]
                    )
                elif price_verdict in ('illegal', 'high'):
                    # Same category, climate-suitable, cheaper than quoted price
                    alts_qs = Product.objects.filter(
                        category=product.category, is_active=True,
                        price__lt=quoted_price,
                    ).exclude(pk=product.pk)
                    if selected_climate:
                        alts_qs = alts_qs.filter(**{selected_climate: True})
                    alternatives = list(alts_qs.order_by('price')[:2])

                items.append({
                    'product':            product,
                    'quoted_price':       quoted_price,
                    'quantity':           quantity,
                    'line_quoted':        line_quoted,
                    'line_fair':          line_fair,
                    'overcharge':         overcharge,
                    'overcharge_abs':     abs(overcharge),
                    'is_suitable':        is_suitable,
                    'price_verdict':      price_verdict,
                    'price_staleness':    price_staleness,
                    'price_source_badge': price_source_badge,
                    'alternatives':       alternatives,
                })

            if parse_error:
                error = 'Invalid input — please check all price and quantity fields.'
            elif not items:
                error = 'Please add at least one material to analyze.'
            else:
                illegal_items = [i for i in items if i['price_verdict'] == 'illegal']
                high_items    = [i for i in items if i['price_verdict'] == 'high']
                bad_climate   = [i for i in items if not i['is_suitable']]

                # Staleness banner: show if ANY item has stale or unknown price date
                has_stale_prices = any(
                    i['price_staleness'] in ('stale', 'unknown') for i in items
                )

                total_difference = total_quoted - total_fair   # positive = overpaying
                report = {
                    'items':              items,
                    'total_quoted':       total_quoted,
                    'total_fair':         total_fair,
                    'difference':         total_difference,
                    'difference_abs':     abs(total_difference),
                    'climate_label':      CLIMATE_FILTERS[selected_climate],
                    'climate_key':        selected_climate,
                    'unsuitable_count':   len(bad_climate),
                    'illegal_count':      len(illegal_items),
                    'high_count':         len(high_items),
                    'all_fair':           not illegal_items and not high_items and not bad_climate,
                    'has_stale_prices':   has_stale_prices,
                }

    # AI Bill Analyzer session data
    bill_analysis    = request.session.get('bill_analysis')
    bill_filename    = request.session.get('bill_filename', '')
    bill_history_json = request.session.get('bill_history_seed', 'null')
    bill_error       = request.session.pop('bill_error', None)
    request.session.modified = True

    return render(request, 'products/analyzer.html', {
        'products_qs':        products_qs,
        'climate_filters':    CLIMATE_FILTERS.items(),
        'selected_climate':   selected_climate,
        'report':             report,
        'error':              error,
        # AI analyzer
        'bill_analysis':      bill_analysis,
        'bill_filename':      bill_filename,
        'bill_history_json':  bill_history_json,
        'bill_error':         bill_error,
    })


# ─────────────────────────────────────────────────────────────────
# SAVED MATERIALS (WISHLIST)
# ─────────────────────────────────────────────────────────────────

@login_required
def toggle_save(request, slug):
    """POST /materials/save/<slug>/ — toggle saved/unsaved for a product."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    product = get_object_or_404(Product, slug=slug, is_active=True)
    saved_obj, created = SavedMaterial.objects.get_or_create(
        user=request.user,
        product=product,
    )
    if not created:
        saved_obj.delete()
        is_saved = False
    else:
        is_saved = True

    return render(request, 'products/partials/save_button.html', {
        'product': product,
        'is_saved': is_saved,
    })


@login_required
def saved_materials_view(request):
    """GET /saved/ — list all materials saved by the current user."""
    saved = (
        SavedMaterial.objects
        .filter(user=request.user)
        .select_related('product')
        .order_by('-saved_at')
    )
    return render(request, 'products/saved_materials.html', {'saved': saved})


@login_required
def remove_saved(request, slug):
    """
    POST /saved/remove/<slug>/ — delete a saved material and return OOB updates.

    Uses HTMX out-of-band swaps so the page updates without a reload:
    - The target card (hx-target="#saved-card-<slug>") is replaced with empty
      string via hx-swap="outerHTML", removing it from the DOM.
    - The count span (#saved-count) is updated via OOB swap.
    - If no items remain, the empty state (#empty-state) is revealed via OOB swap.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    product = get_object_or_404(Product, slug=slug)
    SavedMaterial.objects.filter(user=request.user, product=product).delete()

    new_count = SavedMaterial.objects.filter(user=request.user).count()
    plural = 's' if new_count != 1 else ''

    # OOB swap: update the header count text
    count_oob = (
        f'<span id="saved-count" hx-swap-oob="true">'
        f'{new_count} material{plural} saved</span>'
    )

    if new_count == 0:
        browse_url = reverse('product_list')
        empty_oob = (
            '<div id="empty-state" class="saved-empty" hx-swap-oob="true" style="display:block">'
            '<div class="saved-empty-icon">'
            '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06'
            'a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78'
            '1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>'
            '</svg></div>'
            '<h2 class="saved-empty-title">No saved materials yet</h2>'
            '<p class="saved-empty-sub">Browse materials and click \u201cSave Material\u201d to build your list.</p>'
            f'<a href="{browse_url}" class="db-hero-btn db-hero-btn--primary" '
            'style="display:inline-flex;margin-top:8px;">Browse Materials \u2192</a>'
            '</div>'
        )
        return HttpResponse(count_oob + empty_oob)

    return HttpResponse(count_oob)
