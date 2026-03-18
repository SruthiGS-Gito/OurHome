#!/usr/bin/env python3
"""
OurHome Mobile Redesign Audit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run from project root:
    python mobile_redesign_audit.py

What this does:
  1. Reads every CSS file in static/css/
  2. Reads every template in templates/
  3. Analyses current mobile patterns
  4. Generates a full mobile_redesign_report.md  ← human-readable explanation
  5. Generates mobile_redesign.css               ← drop-in CSS with inline comments
  6. Generates mobile_redesign_patch.html        ← JS hamburger + navbar patch snippet

Design reference: Amazon · Myntra · Nykaa mobile patterns
  - Bottom navigation bar
  - Sticky search bar
  - Horizontal product scroll rows
  - Compact list cards (image left, content right)
  - Full-bleed hero
  - Filter drawer (slide-up, not sidebar)
"""

import os
import re
import textwrap
from pathlib import Path
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────
CSS_DIR       = Path("static/css")
TEMPLATES_DIR = Path("templates")
OUTPUT_CSS    = Path("static/css/mobile_redesign.css")
OUTPUT_REPORT = Path("mobile_redesign_report.md")
OUTPUT_PATCH  = Path("mobile_redesign_patch.html")

BRAND_PINK    = "#e91e8c"
BRAND_PURPLE  = "#7c3aed"
BREAKPOINT    = "768px"

# ── Helpers ──────────────────────────────────────────────────────────────────

def read_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""

def find_css_classes(css_text):
    """Extract all class selectors from CSS."""
    return re.findall(r'\.([\w-]+)\s*[{,]', css_text)

def find_template_classes(html_text):
    """Extract class names used in templates."""
    return re.findall(r'class=["\']([^"\']+)["\']', html_text)

def detect_existing_mobile_rules(css_text):
    """Find any existing @media mobile blocks."""
    blocks = re.findall(
        r'@media[^{]*max-width\s*:\s*(\d+)px[^{]*\{([\s\S]*?)(?=@media|\Z)',
        css_text
    )
    return blocks

def analyse_css_file(filepath):
    """Return a dict of findings for one CSS file."""
    text = read_file(filepath)
    if not text.strip():
        return None

    existing_mobile = detect_existing_mobile_rules(text)
    all_classes     = find_css_classes(text)
    has_grid        = 'grid' in text or 'display: grid' in text
    has_flex        = 'flex' in text
    has_overflow    = 'overflow' in text

    # Detect specific patterns
    grid_defs   = re.findall(r'grid-template-columns\s*:\s*([^;]+);', text)
    flex_defs   = re.findall(r'display\s*:\s*flex', text)
    font_sizes  = re.findall(r'font-size\s*:\s*([^;]+);', text)
    paddings    = re.findall(r'padding\s*:\s*([^;]+);', text)
    positions   = re.findall(r'position\s*:\s*(absolute|fixed|sticky)', text)

    return {
        "file":           str(filepath),
        "size":           len(text),
        "classes":        list(set(all_classes)),
        "existing_mobile": existing_mobile,
        "has_grid":       has_grid,
        "has_flex":       has_flex,
        "has_overflow":   has_overflow,
        "grid_defs":      grid_defs,
        "flex_defs":      flex_defs,
        "font_sizes":     list(set(font_sizes)),
        "positions":      positions,
        "raw":            text,
    }

def analyse_template(filepath):
    """Return key structural classes used in a template."""
    text = read_file(filepath)
    if not text.strip():
        return None
    raw_classes = find_template_classes(text)
    all_classes = []
    for group in raw_classes:
        all_classes.extend(group.split())
    unique = list(set(all_classes))

    # Detect structural patterns
    has_card      = any('card' in c for c in unique)
    has_grid      = any('grid' in c for c in unique)
    has_nav       = any(c in unique for c in ['navbar','nav','nav-links','hamburger'])
    has_filter    = any('filter' in c for c in unique)
    has_hero      = any('hero' in c for c in unique)
    has_dashboard = any('dashboard' in c for c in unique)
    has_product   = any(c in unique for c in ['product','material','catalog'])
    has_directory = any(c in unique for c in ['contractor','designer','provider','directory'])

    return {
        "file":          str(filepath),
        "classes":       unique,
        "has_card":      has_card,
        "has_grid":      has_grid,
        "has_nav":       has_nav,
        "has_filter":    has_filter,
        "has_hero":      has_hero,
        "has_dashboard": has_dashboard,
        "has_product":   has_product,
        "has_directory": has_directory,
    }

# ── CSS Generation ────────────────────────────────────────────────────────────

def generate_mobile_css(css_analyses, template_analyses):
    """Generate the complete mobile_redesign.css with inline rationale comments."""

    # Collect all class names seen across codebase
    all_css_classes  = set()
    all_tmpl_classes = set()
    for a in css_analyses.values():
        if a:
            all_css_classes.update(a['classes'])
    for a in template_analyses.values():
        if a:
            all_tmpl_classes.update(a['classes'])
    live_classes = all_css_classes | all_tmpl_classes

    def has(*names):
        return any(n in live_classes for n in names)

    lines = []
    def w(s=""):
        lines.append(s)

    w("/*")
    w(" * OurHome — Mobile Redesign CSS")
    w(f" * Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    w(" * Reference: Amazon · Myntra · Nykaa mobile patterns")
    w(" * Drop-in file — does NOT touch desktop styles (all rules inside @media)")
    w(" * Import in base.html AFTER all other CSS links:")
    w(' *   <link rel="stylesheet" href="{% static \'css/mobile_redesign.css\' %}">')
    w(" */")
    w()

    # ── CSS Custom Properties (inherit from existing brand) ──────────────────
    w("/* ─────────────────────────────────────────────────────────────────────")
    w("   DESIGN TOKENS")
    w("   Why: Centralised variables mean one edit fixes colours everywhere.")
    w("   These mirror OurHome's existing pink/purple brand palette.")
    w("───────────────────────────────────────────────────────────────────── */")
    w(":root {")
    w(f"  --m-primary:      {BRAND_PINK};")
    w(f"  --m-primary-dark: #c2185b;")
    w(f"  --m-accent:       {BRAND_PURPLE};")
    w("  --m-bg:           #f7f7f7;")
    w("  --m-surface:      #ffffff;")
    w("  --m-border:       #ebebeb;")
    w("  --m-text-primary: #1a1a1a;")
    w("  --m-text-secondary: #666666;")
    w("  --m-text-muted:   #aaaaaa;")
    w("  --m-radius-sm:    8px;")
    w("  --m-radius-md:    12px;")
    w("  --m-radius-lg:    16px;")
    w("  --m-shadow-sm:    0 1px 4px rgba(0,0,0,0.07);")
    w("  --m-shadow-md:    0 2px 12px rgba(0,0,0,0.10);")
    w("  --m-nav-height:   56px;")
    w("  --m-bottom-nav:   60px;")
    w("}")
    w()

    w(f"@media (max-width: {BREAKPOINT}) {{")
    w()

    # ── 1. GLOBAL RESETS ──────────────────────────────────────────────────────
    w("  /* ═══════════════════════════════════════════════════════════════════")
    w("     1. GLOBAL RESETS")
    w("     WHY: Mobile browsers add inconsistent default padding/margins.")
    w("     Box-sizing border-box prevents layout overflow from padding.")
    w("  ══════════════════════════════════════════════════════════════════════ */")
    w()
    w("  *, *::before, *::after {")
    w("    box-sizing: border-box;")
    w("  }")
    w()
    w("  body {")
    w("    background: var(--m-bg);")
    w("    /* Add bottom padding so content isn't hidden behind bottom nav */")
    w("    padding-bottom: var(--m-bottom-nav);")
    w("    overflow-x: hidden;")
    w("  }")
    w()
    w("  /* Prevent any element from causing horizontal scroll */")
    w("  .container, .page-wrapper, main, section {")
    w("    max-width: 100vw;")
    w("    overflow-x: hidden;")
    w("  }")
    w()

    # ── 2. TOP NAVBAR ─────────────────────────────────────────────────────────
    w("  /* ═══════════════════════════════════════════════════════════════════")
    w("     2. TOP NAVBAR")
    w("     WHY: Screenshots show 2-row navbar (links wrap below Sign In).")
    w("     Amazon/Myntra pattern: one sticky row = logo + hamburger + avatar.")
    w("     Nav links collapse into a full-screen slide-down drawer.")
    w("  ══════════════════════════════════════════════════════════════════════ */")
    w()
    w("  nav, .navbar, header nav, .nav-container {")
    w("    position: sticky;")
    w("    top: 0;")
    w("    z-index: 200;")
    w("    background: var(--m-surface);")
    w("    border-bottom: 1px solid var(--m-border);")
    w("    height: var(--m-nav-height);")
    w("    display: flex;")
    w("    align-items: center;")
    w("    justify-content: space-between;")
    w("    padding: 0 1rem;")
    w("    box-shadow: var(--m-shadow-sm);")
    w("  }")
    w()
    w("  /* Hide desktop nav links — shown only when .open toggled by JS */")
    w("  .nav-links, .navbar-links, nav ul {")
    w("    display: none;")
    w("    position: fixed;")
    w("    top: var(--m-nav-height);")
    w("    left: 0; right: 0; bottom: 0;")
    w("    background: rgba(255,255,255,0.98);")
    w("    backdrop-filter: blur(8px);")
    w("    flex-direction: column;")
    w("    padding: 1.5rem 1.5rem 2rem;")
    w("    gap: 0;")
    w("    z-index: 199;")
    w("    overflow-y: auto;")
    w("    animation: slideDown 0.22s ease;")
    w("  }")
    w()
    w("  @keyframes slideDown {")
    w("    from { transform: translateY(-8px); opacity: 0; }")
    w("    to   { transform: translateY(0);    opacity: 1; }")
    w("  }")
    w()
    w("  .nav-links.open, .navbar-links.open, nav ul.open {")
    w("    display: flex;")
    w("  }")
    w()
    w("  .nav-links a, .navbar-links a, nav ul li a {")
    w("    display: block;")
    w("    padding: 1rem 0;")
    w("    font-size: 1.05rem;")
    w("    font-weight: 500;")
    w("    color: var(--m-text-primary);")
    w("    border-bottom: 1px solid var(--m-border);")
    w("    text-decoration: none;")
    w("  }")
    w()
    w("  .nav-links a:last-child, nav ul li:last-child a {")
    w("    border-bottom: none;")
    w("  }")
    w()
    w("  /* Sign In button inside drawer */")
    w("  .nav-links .btn-signin, .nav-cta {")
    w("    display: block;")
    w("    margin-top: 1.5rem;")
    w("    padding: 0.85rem;")
    w("    background: var(--m-primary);")
    w("    color: #fff;")
    w("    border-radius: var(--m-radius-md);")
    w("    text-align: center;")
    w("    font-weight: 700;")
    w("    font-size: 1rem;")
    w("  }")
    w()
    w("  /* Hamburger button */")
    w("  .hamburger, .nav-toggle, .menu-toggle {")
    w("    display: flex !important;")
    w("    flex-direction: column;")
    w("    justify-content: center;")
    w("    gap: 5px;")
    w("    width: 36px;")
    w("    height: 36px;")
    w("    padding: 6px;")
    w("    background: none;")
    w("    border: none;")
    w("    cursor: pointer;")
    w("  }")
    w()
    w("  .hamburger span {")
    w("    display: block;")
    w("    width: 22px;")
    w("    height: 2px;")
    w("    background: var(--m-text-primary);")
    w("    border-radius: 2px;")
    w("    transition: transform 0.25s, opacity 0.2s;")
    w("  }")
    w()
    w("  .hamburger.active span:nth-child(1) { transform: translateY(7px) rotate(45deg); }")
    w("  .hamburger.active span:nth-child(2) { opacity: 0; }")
    w("  .hamburger.active span:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }")
    w()
    w("  /* User avatar pill */")
    w("  .profile-avatar, .user-avatar-wrapper img {")
    w("    width: 32px;")
    w("    height: 32px;")
    w("    border-radius: 50%;")
    w("    object-fit: cover;")
    w("    border: 2px solid var(--m-border);")
    w("  }")
    w()

    # ── 3. STICKY SEARCH BAR ─────────────────────────────────────────────────
    w("  /* ═══════════════════════════════════════════════════════════════════")
    w("     3. STICKY SEARCH BAR")
    w("     WHY: Amazon/Myntra keep search always accessible below navbar.")
    w("     Floating search wastes a tap on every page.")
    w("  ══════════════════════════════════════════════════════════════════════ */")
    w()
    w("  .search-bar-wrapper, .global-search, form.search-form {")
    w("    position: sticky;")
    w("    top: var(--m-nav-height);")
    w("    z-index: 190;")
    w("    background: var(--m-surface);")
    w("    padding: 0.5rem 1rem;")
    w("    border-bottom: 1px solid var(--m-border);")
    w("    display: flex;")
    w("    gap: 0;")
    w("    box-shadow: var(--m-shadow-sm);")
    w("  }")
    w()
    w("  .search-bar-wrapper input, .global-search input {")
    w("    flex: 1;")
    w("    padding: 0.6rem 1rem;")
    w("    font-size: 0.95rem;")
    w("    border: 1.5px solid var(--m-border);")
    w("    border-right: none;")
    w("    border-radius: var(--m-radius-sm) 0 0 var(--m-radius-sm);")
    w("    outline: none;")
    w("    background: #f9f9f9;")
    w("  }")
    w()
    w("  .search-bar-wrapper button, .global-search button {")
    w("    padding: 0.6rem 1rem;")
    w("    background: var(--m-primary);")
    w("    border: none;")
    w("    border-radius: 0 var(--m-radius-sm) var(--m-radius-sm) 0;")
    w("    color: #fff;")
    w("    cursor: pointer;")
    w("  }")
    w()

    # ── 4. BOTTOM NAVIGATION BAR ─────────────────────────────────────────────
    w("  /* ═══════════════════════════════════════════════════════════════════")
    w("     4. BOTTOM NAVIGATION BAR")
    w("     WHY: Amazon/Myntra/Nykaa all use bottom nav on mobile.")
    w("     Thumb-reachable navigation is a core mobile UX principle.")
    w("     Requires adding id='bottom-nav' to base.html (see patch file).")
    w("  ══════════════════════════════════════════════════════════════════════ */")
    w()
    w("  #bottom-nav {")
    w("    position: fixed;")
    w("    bottom: 0; left: 0; right: 0;")
    w("    height: var(--m-bottom-nav);")
    w("    background: var(--m-surface);")
    w("    border-top: 1px solid var(--m-border);")
    w("    display: flex;")
    w("    align-items: stretch;")
    w("    z-index: 300;")
    w("    box-shadow: 0 -2px 12px rgba(0,0,0,0.08);")
    w("  }")
    w()
    w("  #bottom-nav a {")
    w("    flex: 1;")
    w("    display: flex;")
    w("    flex-direction: column;")
    w("    align-items: center;")
    w("    justify-content: center;")
    w("    gap: 3px;")
    w("    font-size: 0.62rem;")
    w("    font-weight: 600;")
    w("    color: var(--m-text-secondary);")
    w("    text-decoration: none;")
    w("    letter-spacing: 0.02em;")
    w("    transition: color 0.15s;")
    w("  }")
    w()
    w("  #bottom-nav a.active, #bottom-nav a:hover {")
    w("    color: var(--m-primary);")
    w("  }")
    w()
    w("  #bottom-nav a svg {")
    w("    width: 22px;")
    w("    height: 22px;")
    w("  }")
    w()
    w("  #bottom-nav a.active svg { stroke: var(--m-primary); }")
    w()

    # ── 5. HERO SECTION ───────────────────────────────────────────────────────
    w("  /* ═══════════════════════════════════════════════════════════════════")
    w("     5. HERO SECTION")
    w("     WHY: Full-bleed heroes with large text perform better on mobile.")
    w("     Desktop heroes often have excessive padding on small screens.")
    w("  ══════════════════════════════════════════════════════════════════════ */")
    w()
    w("  .hero-section, .hero-banner {")
    w("    padding: 2rem 1.25rem 2.5rem;")
    w("    border-radius: 0;")
    w("    min-height: unset;")
    w("  }")
    w()
    w("  .hero-section h1, .hero-banner h1 {")
    w("    font-size: clamp(1.8rem, 7vw, 2.4rem);")
    w("    line-height: 1.15;")
    w("  }")
    w()
    w("  .hero-section p, .hero-banner p {")
    w("    font-size: 0.95rem;")
    w("  }")
    w()
    w("  .hero-btns, .hero-actions {")
    w("    flex-direction: column;")
    w("    gap: 0.75rem;")
    w("    margin-top: 1.25rem;")
    w("  }")
    w()
    w("  .hero-btns a, .hero-actions a {")
    w("    width: 100%;")
    w("    text-align: center;")
    w("    padding: 0.85rem;")
    w("    border-radius: var(--m-radius-md);")
    w("    font-size: 1rem;")
    w("    font-weight: 700;")
    w("  }")
    w()

    # ── 6. CLIMATE ZONE CARDS ────────────────────────────────────────────────
    w("  /* ═══════════════════════════════════════════════════════════════════")
    w("     6. CLIMATE ZONE CARDS")
    w("     WHY: 2-column grid is already correct for mobile but cards need")
    w("     better spacing, icon sizing, and truncation guards.")
    w("  ══════════════════════════════════════════════════════════════════════ */")
    w()
    w("  .climate-grid, .climate-cards-grid {")
    w("    grid-template-columns: repeat(2, 1fr);")
    w("    gap: 0.75rem;")
    w("    padding: 0.5rem 1rem 1rem;")
    w("  }")
    w()
    w("  .climate-card {")
    w("    padding: 1rem 0.75rem;")
    w("    border-radius: var(--m-radius-md);")
    w("    background: var(--m-surface);")
    w("    border: 1px solid var(--m-border);")
    w("    box-shadow: var(--m-shadow-sm);")
    w("    text-align: center;")
    w("  }")
    w()
    w("  .climate-card svg, .climate-icon { width: 36px; height: 36px; }")
    w()
    w("  .climate-card h3 {")
    w("    font-size: 0.9rem;")
    w("    font-weight: 700;")
    w("    margin: 0.4rem 0 0.2rem;")
    w("  }")
    w()
    w("  .climate-card .region-text, .climate-card p {")
    w("    font-size: 0.72rem;")
    w("    color: var(--m-text-secondary);")
    w("    line-height: 1.3;")
    w("    /* Prevent overflow on long region names */")
    w("    overflow: hidden;")
    w("    display: -webkit-box;")
    w("    -webkit-line-clamp: 2;")
    w("    -webkit-box-orient: vertical;")
    w("  }")
    w()
    w("  .climate-card .material-count, .climate-card a {")
    w("    font-size: 0.82rem;")
    w("    font-weight: 700;")
    w("    color: var(--m-primary);")
    w("    margin-top: 0.5rem;")
    w("    display: block;")
    w("  }")
    w()

    # ── 7. CATEGORY TYPE GRID (Cement, Steel, Tiles…) ────────────────────────
    w("  /* ═══════════════════════════════════════════════════════════════════")
    w("     7. MATERIAL CATEGORY ICON GRID")
    w("     WHY: Nykaa/Myntra use 4-per-row category icons on mobile.")
    w("     Switching from 2-col to 4-col gives more context at a glance.")
    w("  ══════════════════════════════════════════════════════════════════════ */")
    w()
    w("  .category-grid, .material-type-grid {")
    w("    grid-template-columns: repeat(4, 1fr);")
    w("    gap: 0.5rem;")
    w("    padding: 0.5rem 1rem;")
    w("  }")
    w()
    w("  .category-card, .material-type-card {")
    w("    padding: 0.85rem 0.4rem;")
    w("    border-radius: var(--m-radius-sm);")
    w("    background: var(--m-surface);")
    w("    display: flex;")
    w("    flex-direction: column;")
    w("    align-items: center;")
    w("    gap: 0.35rem;")
    w("    border: 1px solid var(--m-border);")
    w("    box-shadow: var(--m-shadow-sm);")
    w("  }")
    w()
    w("  .category-card svg, .category-icon { width: 28px; height: 28px; }")
    w()
    w("  .category-card span, .category-card p {")
    w("    font-size: 0.7rem;")
    w("    font-weight: 600;")
    w("    text-align: center;")
    w("    color: var(--m-text-primary);")
    w("    line-height: 1.2;")
    w("  }")
    w()

    # ── 8. PRODUCT CARDS — MYNTRA HORIZONTAL LIST ────────────────────────────
    w("  /* ═══════════════════════════════════════════════════════════════════")
    w("     8. MATERIAL / PRODUCT CARDS — MYNTRA HORIZONTAL LIST CARD")
    w("     WHY: Full vertical cards on mobile waste 300-400px per item.")
    w("     Myntra/Amazon list view = image left (fixed 100px) + content right.")
    w("     Users see 3× more items without scrolling.")
    w("     The catalog grid must collapse to a single column to allow this.")
    w("  ══════════════════════════════════════════════════════════════════════ */")
    w()
    w("  /* Collapse grid → single column list */")
    w("  .materials-grid, .products-grid, .catalog-grid {")
    w("    display: flex !important;")
    w("    flex-direction: column;")
    w("    gap: 0;")
    w("    padding: 0;")
    w("    background: var(--m-bg);")
    w("  }")
    w()
    w("  /* Horizontal list card */")
    w("  .material-card, .product-card {")
    w("    display: flex !important;")
    w("    flex-direction: row !important;")
    w("    align-items: stretch;")
    w("    background: var(--m-surface);")
    w("    border-radius: 0 !important;")
    w("    border: none;")
    w("    border-bottom: 8px solid var(--m-bg);")
    w("    padding: 0 !important;")
    w("    box-shadow: none;")
    w("    overflow: hidden;")
    w("    position: relative;")
    w("    min-height: 110px;")
    w("  }")
    w()
    w("  /* Image — fixed 110px square */")
    w("  .material-card .card-image,")
    w("  .material-card img:first-of-type,")
    w("  .product-card .card-image,")
    w("  .product-card img:first-of-type {")
    w("    width: 110px !important;")
    w("    min-width: 110px !important;")
    w("    height: 110px !important;")
    w("    object-fit: cover;")
    w("    flex-shrink: 0;")
    w("    border-radius: 0;")
    w("  }")
    w()
    w("  /* Content area */")
    w("  .material-card .card-body,")
    w("  .material-card .card-content,")
    w("  .product-card .card-body,")
    w("  .product-card .card-content {")
    w("    flex: 1;")
    w("    min-width: 0;")
    w("    padding: 0.65rem 0.75rem;")
    w("    display: flex;")
    w("    flex-direction: column;")
    w("    justify-content: space-between;")
    w("    overflow: hidden;")
    w("  }")
    w()
    w("  /* Category + IS badge row */")
    w("  .material-card .badge-row {")
    w("    display: flex;")
    w("    gap: 0.3rem;")
    w("    align-items: center;")
    w("    margin-bottom: 0.2rem;")
    w("    flex-wrap: nowrap;")
    w("    overflow: hidden;")
    w("  }")
    w()
    w("  .material-card .category-badge, .product-card .category-badge {")
    w("    font-size: 0.6rem;")
    w("    font-weight: 800;")
    w("    letter-spacing: 0.05em;")
    w("    text-transform: uppercase;")
    w("    white-space: nowrap;")
    w("  }")
    w()
    w("  .material-card .is-badge, .product-card .is-standard {")
    w("    font-size: 0.6rem;")
    w("    color: var(--m-text-muted);")
    w("    white-space: nowrap;")
    w("  }")
    w()
    w("  /* Product name — max 2 lines */")
    w("  .material-card .card-title, .material-card h3,")
    w("  .product-card .card-title,  .product-card h3 {")
    w("    font-size: 0.88rem;")
    w("    font-weight: 700;")
    w("    line-height: 1.25;")
    w("    margin: 0 0 0.15rem;")
    w("    color: var(--m-text-primary);")
    w("    display: -webkit-box;")
    w("    -webkit-line-clamp: 2;")
    w("    -webkit-box-orient: vertical;")
    w("    overflow: hidden;")
    w("  }")
    w()
    w("  /* Brand */")
    w("  .material-card .brand, .product-card .brand {")
    w("    font-size: 0.75rem;")
    w("    color: var(--m-text-muted);")
    w("    margin-bottom: 0.2rem;")
    w("  }")
    w()
    w("  /* Price row */")
    w("  .material-card .price, .product-card .price {")
    w("    font-size: 1rem;")
    w("    font-weight: 800;")
    w("    color: var(--m-text-primary);")
    w("  }")
    w()
    w("  .material-card .mrp, .product-card .mrp {")
    w("    font-size: 0.72rem;")
    w("    text-decoration: line-through;")
    w("    color: var(--m-text-muted);")
    w("    margin-left: 0.25rem;")
    w("  }")
    w()
    w("  /* Climate tags — scrollable row, no wrap */")
    w("  .material-card .climate-tags, .product-card .climate-tags {")
    w("    display: flex;")
    w("    flex-wrap: nowrap;")
    w("    gap: 0.2rem;")
    w("    overflow-x: auto;")
    w("    scrollbar-width: none;")
    w("    margin: 0.2rem 0;")
    w("  }")
    w("  .material-card .climate-tags::-webkit-scrollbar { display: none; }")
    w()
    w("  .material-card .climate-tag, .product-card .climate-tag {")
    w("    font-size: 0.6rem;")
    w("    padding: 0.12rem 0.4rem;")
    w("    border-radius: 3px;")
    w("    white-space: nowrap;")
    w("    flex-shrink: 0;")
    w("  }")
    w()
    w("  /* View Details — small inline link, not full-width button */")
    w("  .material-card .btn-view, .material-card a.btn,")
    w("  .product-card .btn-view,  .product-card a.btn {")
    w("    display: inline-block;")
    w("    font-size: 0.78rem;")
    w("    font-weight: 700;")
    w("    color: var(--m-primary);")
    w("    padding: 0.3rem 0;")
    w("    margin-top: 0.2rem;")
    w("    background: transparent;")
    w("    border: none;")
    w("    text-decoration: underline;")
    w("    width: auto;")
    w("  }")
    w()
    w("  /* Popular / sale badge — top-left of image */")
    w("  .badge-popular, .popular-badge {")
    w("    position: absolute;")
    w("    top: 6px; left: 6px;")
    w("    font-size: 0.6rem;")
    w("    font-weight: 800;")
    w("    padding: 0.2rem 0.5rem;")
    w("    border-radius: 3px;")
    w("    z-index: 2;")
    w("    text-transform: uppercase;")
    w("    letter-spacing: 0.04em;")
    w("  }")
    w()

    # ── 9. CATEGORY PILL TABS ────────────────────────────────────────────────
    w("  /* ═══════════════════════════════════════════════════════════════════")
    w("     9. CATEGORY PILL TABS (All · Cement · Steel · Bricks…)")
    w("     WHY: Amazon/Myntra use sticky horizontal scroll pill tabs.")
    w("     They must not wrap to 2+ rows — horizontal scroll with snap.")
    w("  ══════════════════════════════════════════════════════════════════════ */")
    w()
    w("  .category-tabs, .material-categories {")
    w("    display: flex;")
    w("    overflow-x: auto;")
    w("    scrollbar-width: none;")
    w("    -webkit-overflow-scrolling: touch;")
    w("    gap: 0.5rem;")
    w("    padding: 0.6rem 1rem;")
    w("    background: var(--m-surface);")
    w("    border-bottom: 1px solid var(--m-border);")
    w("    position: sticky;")
    w("    top: calc(var(--m-nav-height) + 44px);  /* below navbar + search */")
    w("    z-index: 180;")
    w("    scroll-snap-type: x mandatory;")
    w("  }")
    w("  .category-tabs::-webkit-scrollbar { display: none; }")
    w()
    w("  .category-tab, .category-pill {")
    w("    flex-shrink: 0;")
    w("    white-space: nowrap;")
    w("    font-size: 0.82rem;")
    w("    font-weight: 600;")
    w("    padding: 0.4rem 1rem;")
    w("    border-radius: 20px;")
    w("    border: 1.5px solid var(--m-border);")
    w("    background: var(--m-surface);")
    w("    color: var(--m-text-primary);")
    w("    scroll-snap-align: start;")
    w("    cursor: pointer;")
    w("  }")
    w()
    w("  .category-tab.active, .category-pill.active {")
    w("    background: var(--m-primary);")
    w("    color: #fff;")
    w("    border-color: var(--m-primary);")
    w("  }")
    w()

    # ── 10. FILTER BAR ───────────────────────────────────────────────────────
    w("  /* ═══════════════════════════════════════════════════════════════════")
    w("     10. FILTER BAR")
    w("     WHY: Filter dropdowns in a horizontal row collapse on mobile.")
    w("     Myntra uses a 'Filter' trigger button that opens a bottom sheet.")
    w("     Here we stack them vertically as a simpler fallback.")
    w("  ══════════════════════════════════════════════════════════════════════ */")
    w()
    w("  .filter-bar, .catalog-filters {")
    w("    flex-direction: column;")
    w("    gap: 0.5rem;")
    w("    padding: 0.75rem 1rem;")
    w("    background: var(--m-surface);")
    w("    border-bottom: 1px solid var(--m-border);")
    w("  }")
    w()
    w("  .filter-bar select, .catalog-filters select,")
    w("  .filter-bar .filter-group, .catalog-filters .filter-group {")
    w("    width: 100%;")
    w("    font-size: 0.88rem;")
    w("    padding: 0.55rem 0.75rem;")
    w("    border-radius: var(--m-radius-sm);")
    w("    border: 1.5px solid var(--m-border);")
    w("    background: #fafafa;")
    w("  }")
    w()

    # ── 11. DIRECTORY — PROVIDER CARDS ───────────────────────────────────────
    w("  /* ═══════════════════════════════════════════════════════════════════")
    w("     11. DIRECTORY — CONTRACTOR & DESIGNER CARDS")
    w("     WHY: Screenshots show purple ghost box (filter panel) overlapping")
    w("     results. Root cause: filter panel is position:absolute/fixed and")
    w("     not properly cleared in mobile flow.")
    w("     Fix: force filter panel to static, full-width, stacked above results.")
    w("     Card layout: compact list — 56px avatar left, details right.")
    w("  ══════════════════════════════════════════════════════════════════════ */")
    w()
    w("  /* Fix filter panel overlap (the purple ghost box in screenshots) */")
    w("  .filter-panel, .directory-filters, .filter-sidebar {")
    w("    position: static !important;")
    w("    width: 100% !important;")
    w("    float: none !important;")
    w("    z-index: auto !important;")
    w("    border-radius: 0;")
    w("    padding: 1rem;")
    w("    background: #fafafa;")
    w("    border-bottom: 8px solid var(--m-bg);")
    w("    margin-bottom: 0;")
    w("  }")
    w()
    w("  .directory-layout, .directory-container {")
    w("    display: flex !important;")
    w("    flex-direction: column !important;")
    w("    gap: 0;")
    w("  }")
    w()
    w("  .directory-results, .provider-list {")
    w("    display: flex !important;")
    w("    flex-direction: column;")
    w("    gap: 0;")
    w("    padding: 0;")
    w("  }")
    w()
    w("  /* Provider card — compact list item */")
    w("  .provider-card, .contractor-card, .designer-card {")
    w("    border-radius: 0 !important;")
    w("    border: none;")
    w("    border-bottom: 8px solid var(--m-bg);")
    w("    background: var(--m-surface);")
    w("    overflow: hidden;")
    w("    box-shadow: none;")
    w("  }")
    w()
    w("  /* Banner strip — shorter */")
    w("  .provider-card .card-banner, .contractor-card .card-banner,")
    w("  .designer-card .card-banner, .banner-strip {")
    w("    height: 48px !important;")
    w("    min-height: 48px !important;")
    w("  }")
    w()
    w("  /* Card body */")
    w("  .provider-card .card-body, .contractor-card .card-body,")
    w("  .designer-card .card-body {")
    w("    padding: 0.75rem 1rem;")
    w("  }")
    w()
    w("  /* Avatar — pull up over banner */")
    w("  .provider-card .avatar, .contractor-card .avatar,")
    w("  .designer-card .avatar, .provider-avatar {")
    w("    width: 52px !important;")
    w("    height: 52px !important;")
    w("    min-width: 52px;")
    w("    font-size: 1rem !important;")
    w("    margin-top: -26px;")
    w("    border: 2.5px solid #fff;")
    w("    border-radius: 50%;")
    w("  }")
    w()
    w("  /* Info row beside avatar */")
    w("  .provider-card .provider-meta { margin-top: 0.4rem; }")
    w()
    w("  .provider-card h3, .contractor-card h3, .designer-card h3 {")
    w("    font-size: 0.95rem;")
    w("    font-weight: 700;")
    w("    margin: 0 0 0.1rem;")
    w("  }")
    w()
    w("  .provider-card .provider-role, .card-role {")
    w("    font-size: 0.78rem;")
    w("    color: var(--m-text-secondary);")
    w("  }")
    w()
    w("  .provider-card .stats-row, .provider-stats {")
    w("    font-size: 0.8rem;")
    w("    color: var(--m-text-secondary);")
    w("    display: flex;")
    w("    flex-wrap: wrap;")
    w("    gap: 0.5rem;")
    w("    margin: 0.35rem 0;")
    w("  }")
    w()
    w("  .provider-card .price-range, .contractor-card .rate-range {")
    w("    font-size: 0.88rem;")
    w("    font-weight: 700;")
    w("    color: var(--m-primary);")
    w("    margin: 0.3rem 0;")
    w("  }")
    w()
    w("  /* HIDE spec tags on mobile — they overflow and clutter */")
    w("  .provider-card .spec-tags, .contractor-card .spec-tags,")
    w("  .designer-card .spec-tags, .specialization-tags {")
    w("    display: none !important;")
    w("  }")
    w()
    w("  /* Verified badge — inline, not absolute */")
    w("  .verified-badge {")
    w("    font-size: 0.7rem;")
    w("    padding: 0.2rem 0.55rem;")
    w("    border-radius: 20px;")
    w("    display: inline-flex;")
    w("    align-items: center;")
    w("    gap: 0.2rem;")
    w("  }")
    w()
    w("  /* View Profile button — full width */")
    w("  .provider-card a.btn, .provider-card .btn-profile,")
    w("  .contractor-card .btn-profile, .designer-card .btn-profile {")
    w("    display: block;")
    w("    width: 100%;")
    w("    text-align: center;")
    w("    padding: 0.65rem;")
    w("    border-radius: var(--m-radius-sm);")
    w("    font-size: 0.9rem;")
    w("    font-weight: 700;")
    w("    margin-top: 0.65rem;")
    w("  }")
    w()

    # ── 12. DASHBOARD ────────────────────────────────────────────────────────
    w("  /* ═══════════════════════════════════════════════════════════════════")
    w("     12. DASHBOARD")
    w("     WHY: Desktop dashboard cards are wide tiles. On mobile they should")
    w("     be compact list rows (icon left + label+subtitle right).")
    w("     Nykaa/Amazon app pattern: icon 44px, text stacked right.")
    w("  ══════════════════════════════════════════════════════════════════════ */")
    w()
    w("  .dashboard-hero, .welcome-banner {")
    w("    padding: 1.5rem 1.25rem 1.75rem;")
    w("    border-radius: 0;")
    w("  }")
    w()
    w("  .dashboard-hero h1, .welcome-banner h1 {")
    w("    font-size: 1.6rem;")
    w("  }")
    w()
    w("  .dashboard-hero .cta-buttons {")
    w("    flex-direction: column;")
    w("    gap: 0.65rem;")
    w("    margin-top: 1rem;")
    w("  }")
    w()
    w("  .dashboard-hero .cta-buttons a {")
    w("    width: 100%;")
    w("    text-align: center;")
    w("    padding: 0.75rem;")
    w("    border-radius: var(--m-radius-md);")
    w("  }")
    w()
    w("  .dashboard-cards, .dashboard-grid {")
    w("    display: flex !important;")
    w("    flex-direction: column;")
    w("    gap: 0;")
    w("    padding: 0;")
    w("    background: var(--m-bg);")
    w("  }")
    w()
    w("  .dashboard-card, .info-card {")
    w("    display: flex;")
    w("    align-items: center;")
    w("    gap: 1rem;")
    w("    padding: 1rem 1.25rem;")
    w("    background: var(--m-surface);")
    w("    border-bottom: 6px solid var(--m-bg);")
    w("    border-radius: 0 !important;")
    w("    box-shadow: none;")
    w("  }")
    w()
    w("  .dashboard-card .card-icon, .info-card .card-icon {")
    w("    width: 44px;")
    w("    height: 44px;")
    w("    min-width: 44px;")
    w("    border-radius: var(--m-radius-sm);")
    w("    display: flex;")
    w("    align-items: center;")
    w("    justify-content: center;")
    w("    flex-shrink: 0;")
    w("  }")
    w()
    w("  .dashboard-card h3, .info-card h3 {")
    w("    font-size: 0.92rem;")
    w("    font-weight: 700;")
    w("    margin: 0 0 0.1rem;")
    w("  }")
    w()
    w("  .dashboard-card p, .info-card p {")
    w("    font-size: 0.78rem;")
    w("    color: var(--m-text-secondary);")
    w("    margin: 0;")
    w("  }")
    w()
    w("  /* Stat summary cards */")
    w("  .stat-card, .summary-card {")
    w("    background: var(--m-surface);")
    w("    border-bottom: 6px solid var(--m-bg);")
    w("    border-left: 4px solid var(--m-primary);")
    w("    padding: 1rem 1.25rem;")
    w("    border-radius: 0 !important;")
    w("  }")
    w()
    w("  .stat-card .stat-label { font-size: 0.65rem; letter-spacing: 0.06em; }")
    w("  .stat-card .stat-value { font-size: 1.4rem; font-weight: 800; }")
    w("  .stat-card .stat-sub   { font-size: 0.78rem; color: var(--m-text-secondary); }")
    w()
    w("  /* Recently Viewed — horizontal scroll strip */")
    w("  .recently-viewed-scroll, .horizontal-scroll-row {")
    w("    display: flex;")
    w("    overflow-x: auto;")
    w("    gap: 0.75rem;")
    w("    padding: 0.75rem 1rem;")
    w("    scrollbar-width: none;")
    w("    -webkit-overflow-scrolling: touch;")
    w("    scroll-snap-type: x mandatory;")
    w("  }")
    w("  .recently-viewed-scroll::-webkit-scrollbar { display: none; }")
    w()
    w("  .recent-item-card, .mini-product-card {")
    w("    min-width: 130px;")
    w("    max-width: 130px;")
    w("    border-radius: var(--m-radius-sm);")
    w("    overflow: hidden;")
    w("    flex-shrink: 0;")
    w("    background: var(--m-surface);")
    w("    border: 1px solid var(--m-border);")
    w("    box-shadow: var(--m-shadow-sm);")
    w("    scroll-snap-align: start;")
    w("  }")
    w()
    w("  .recent-item-card img { width: 100%; height: 85px; object-fit: cover; }")
    w()
    w("  .recent-item-card .item-info { padding: 0.45rem 0.5rem; }")
    w()
    w("  .recent-item-card h4 {")
    w("    font-size: 0.75rem;")
    w("    font-weight: 600;")
    w("    line-height: 1.2;")
    w("    margin: 0 0 0.1rem;")
    w("    display: -webkit-box;")
    w("    -webkit-line-clamp: 2;")
    w("    -webkit-box-orient: vertical;")
    w("    overflow: hidden;")
    w("  }")
    w()
    w("  .recent-item-card .item-price { font-size: 0.72rem; color: var(--m-text-secondary); }")
    w()

    # ── 13. SECTION HEADERS ──────────────────────────────────────────────────
    w("  /* ═══════════════════════════════════════════════════════════════════")
    w("     13. SECTION HEADERS + VIEW ALL LINKS")
    w("     WHY: Desktop section headings are often 2rem+. On mobile they")
    w("     should be smaller but still bold and authoritative.")
    w("  ══════════════════════════════════════════════════════════════════════ */")
    w()
    w("  .section-header, .section-title-row {")
    w("    display: flex;")
    w("    align-items: center;")
    w("    justify-content: space-between;")
    w("    padding: 1rem 1rem 0.5rem;")
    w("  }")
    w()
    w("  .section-header h2, .section-title {")
    w("    font-size: 1.1rem;")
    w("    font-weight: 800;")
    w("  }")
    w()
    w("  .view-all-link, a.view-all {")
    w("    font-size: 0.82rem;")
    w("    font-weight: 700;")
    w("    color: var(--m-primary);")
    w("    padding: 0.3rem 0.75rem;")
    w("    border: 1.5px solid var(--m-primary);")
    w("    border-radius: 20px;")
    w("    white-space: nowrap;")
    w("  }")
    w()

    # ── 14. ANALYZER CTA ─────────────────────────────────────────────────────
    w("  /* ═══════════════════════════════════════════════════════════════════")
    w("     14. MATERIAL ANALYZER CTA BANNER")
    w("     WHY: The icon overlaps text at narrow widths. Stack vertically,")
    w("     centre-align, reduce icon size for cleaner presentation.")
    w("  ══════════════════════════════════════════════════════════════════════ */")
    w()
    w("  .analyzer-cta, .cta-banner {")
    w("    padding: 2rem 1.5rem;")
    w("    border-radius: 0;")
    w("    text-align: center;")
    w("  }")
    w()
    w("  .analyzer-cta h2, .cta-banner h2 { font-size: 1.6rem; }")
    w("  .analyzer-cta p, .cta-banner p   { font-size: 0.92rem; }")
    w()
    w("  .analyzer-cta .cta-icon, .cta-banner svg,")
    w("  .cta-banner .doc-icon {")
    w("    width: 72px;")
    w("    height: 72px;")
    w("    margin: 1.25rem auto 0;")
    w("    display: block;")
    w("    opacity: 0.85;")
    w("  }")
    w()
    w("  .analyzer-cta .btn, .cta-banner .btn {")
    w("    display: inline-block;")
    w("    margin-top: 1.25rem;")
    w("    padding: 0.8rem 2rem;")
    w("    border-radius: var(--m-radius-md);")
    w("    font-size: 1rem;")
    w("    font-weight: 700;")
    w("  }")
    w()

    # ── 15. UTILITY ──────────────────────────────────────────────────────────
    w("  /* ═══════════════════════════════════════════════════════════════════")
    w("     15. UTILITY — section spacing, typography scale")
    w("     WHY: Desktop sections often have 4-5rem vertical padding.")
    w("     Mobile content density should be higher — 2rem max.")
    w("  ══════════════════════════════════════════════════════════════════════ */")
    w()
    w("  .home-section, .page-section {")
    w("    padding-top: 1.5rem;")
    w("    padding-bottom: 1.5rem;")
    w("  }")
    w()
    w("  h2 { font-size: clamp(1.2rem, 5vw, 1.6rem); }")
    w("  h3 { font-size: clamp(1rem, 4vw, 1.2rem); }")
    w()
    w("  /* Footer */")
    w("  footer, .site-footer {")
    w("    padding-bottom: calc(var(--m-bottom-nav) + 1rem);")
    w("  }")
    w()

    w("}  /* end @media (max-width: 768px) */")
    w()

    return "\n".join(lines)

# ── Report Generation ─────────────────────────────────────────────────────────

def generate_report(css_analyses, template_analyses, changes_summary):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []
    def w(s=""):
        lines.append(s)

    w("# OurHome Mobile Redesign Report")
    w(f"*Generated: {now}*")
    w()
    w("## Reference Design Patterns")
    w("| Platform | Key Mobile Patterns Used |")
    w("|----------|--------------------------|")
    w("| **Amazon** | Sticky search, horizontal scroll carousels, compact list cards, bottom nav |")
    w("| **Myntra** | Horizontal list cards (image left), sticky category pills, slide-up filter drawer |")
    w("| **Nykaa** | 4-col category icons, bottom nav, compact provider rows, scroll-snap carousels |")
    w()
    w("---")
    w()
    w("## Files Analysed")
    w()
    w("### CSS Files")
    for path, a in css_analyses.items():
        if a:
            mob = len(a['existing_mobile'])
            w(f"- **{Path(path).name}** — {a['size']} bytes, {len(a['classes'])} classes, "
              f"{mob} existing @media block(s), "
              f"{'has grid' if a['has_grid'] else ''} {'has flex' if a['has_flex'] else ''}")
    w()
    w("### Templates")
    for path, a in template_analyses.items():
        if a:
            flags = []
            if a['has_nav']:       flags.append('navbar')
            if a['has_hero']:      flags.append('hero')
            if a['has_product']:   flags.append('products')
            if a['has_directory']: flags.append('directory')
            if a['has_dashboard']: flags.append('dashboard')
            if a['has_filter']:    flags.append('filters')
            if flags:
                w(f"- **{Path(path).name}** — {', '.join(flags)}")
    w()
    w("---")
    w()
    w("## What Changed & Why")
    w()
    for section in changes_summary:
        w(f"### {section['title']}")
        w(f"**Problem:** {section['problem']}")
        w()
        w(f"**Fix:** {section['fix']}")
        w()
        w(f"**Reference:** {section['reference']}")
        w()
    w("---")
    w()
    w("## How to Apply")
    w()
    w("```bash")
    w("# 1. The CSS is already written to static/css/mobile_redesign.css")
    w("# 2. Add to your base template <head> AFTER all other CSS:")
    w('#    <link rel="stylesheet" href="{% static \'css/mobile_redesign.css\' %}">')
    w("# 3. Add the bottom nav HTML + hamburger JS from mobile_redesign_patch.html")
    w("# 4. Collect static and redeploy:")
    w("python manage.py collectstatic --noinput")
    w("```")
    w()
    w("## CSS File Map")
    w()
    w("```")
    w("mobile_redesign.css sections:")
    w("  :root        — design tokens (brand colours, spacing, nav heights)")
    w("  §1           — global resets (box-sizing, overflow-x)")
    w("  §2           — top navbar (sticky, hamburger, drawer)")
    w("  §3           — sticky search bar")
    w("  §4           — bottom navigation bar (NEW — requires patch.html)")
    w("  §5           — hero section")
    w("  §6           — climate zone 2-col cards")
    w("  §7           — category icon 4-col grid")
    w("  §8           — product/material cards (Myntra horizontal list)")
    w("  §9           — category pill tabs (horizontal scroll, sticky)")
    w("  §10          — filter bar (stacked vertical)")
    w("  §11          — directory cards + filter overlap fix")
    w("  §12          — dashboard cards + stat cards + scroll carousels")
    w("  §13          — section headers + view-all links")
    w("  §14          — Material Analyzer CTA banner")
    w("  §15          — utility spacing + footer padding")
    w("```")
    w()
    return "\n".join(lines)

# ── Patch HTML Generation ─────────────────────────────────────────────────────

def generate_patch_html():
    return textwrap.dedent("""\
    <!-- ════════════════════════════════════════════════════════════════
         OurHome Mobile Redesign Patch
         Copy the relevant sections into your base.html template.
         ════════════════════════════════════════════════════════════════ -->


    <!-- ── SECTION A: Add inside <head>, AFTER all other CSS links ── -->
    {% load static %}
    <link rel="stylesheet" href="{% static 'css/mobile_redesign.css' %}">


    <!-- ── SECTION B: Bottom Navigation Bar ────────────────────────────
         Add just before </body>.
         Adjust href values to match your actual URL names.
         ─────────────────────────────────────────────────────────────── -->
    <nav id="bottom-nav">
      <a href="{% url 'home' %}" class="{% if request.resolver_match.url_name == 'home' %}active{% endif %}">
        <!-- Home icon -->
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        Home
      </a>
      <a href="{% url 'products:list' %}" class="{% if 'products' in request.resolver_match.app_name %}active{% endif %}">
        <!-- Materials icon -->
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="3" width="20" height="14" rx="2"/>
          <line x1="8" y1="21" x2="16" y2="21"/>
          <line x1="12" y1="17" x2="12" y2="21"/>
        </svg>
        Materials
      </a>
      <a href="{% url 'products:analyzer' %}">
        <!-- Analyzer icon -->
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <polyline points="10 9 9 9 8 9"/>
        </svg>
        Analyzer
      </a>
      <a href="{% url 'users:contractor_list' %}">
        <!-- Contractors icon -->
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
          <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
        Pros
      </a>
      {% if user.is_authenticated %}
      <a href="{% url 'users:dashboard' %}"
         class="{% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}">
        <!-- Profile icon -->
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
        Profile
      </a>
      {% else %}
      <a href="{% url 'users:login' %}">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
          <polyline points="10 17 15 12 10 7"/>
          <line x1="15" y1="12" x2="3" y2="12"/>
        </svg>
        Sign In
      </a>
      {% endif %}
    </nav>


    <!-- ── SECTION C: Hamburger JS ──────────────────────────────────────
         Add inside <body>, before </body>.
         ─────────────────────────────────────────────────────────────── -->
    <script>
    (function() {
      var toggle = document.querySelector('.hamburger, .nav-toggle, .menu-toggle');
      var menu   = document.querySelector('.nav-links, .navbar-links, nav ul');
      var body   = document.body;

      if (!toggle || !menu) return;

      toggle.addEventListener('click', function(e) {
        e.stopPropagation();
        var isOpen = menu.classList.toggle('open');
        toggle.classList.toggle('active', isOpen);
        body.style.overflow = isOpen ? 'hidden' : '';
      });

      // Close on outside click
      document.addEventListener('click', function(e) {
        if (!menu.contains(e.target) && !toggle.contains(e.target)) {
          menu.classList.remove('open');
          toggle.classList.remove('active');
          body.style.overflow = '';
        }
      });

      // Close on nav link click
      menu.querySelectorAll('a').forEach(function(link) {
        link.addEventListener('click', function() {
          menu.classList.remove('open');
          toggle.classList.remove('active');
          body.style.overflow = '';
        });
      });

      // Mark active bottom nav item
      var path = window.location.pathname;
      document.querySelectorAll('#bottom-nav a').forEach(function(a) {
        if (a.getAttribute('href') === path) {
          a.classList.add('active');
        }
      });
    })();
    </script>
    """)

# ── Main ──────────────────────────────────────────────────────────────────────

CHANGES_SUMMARY = [
    {
        "title": "1. Navbar — 2-row collapse → hamburger drawer",
        "problem": "Screenshots show nav links and Sign In button wrapping to a second row, "
                   "consuming ~25% of screen height before any content.",
        "fix": "Nav links hidden by default. Single-row sticky bar: logo + hamburger + avatar. "
               "Links appear in a full-screen overlay drawer on hamburger tap. "
               "Overlay closes on outside click or nav link click. Body scroll locked when open.",
        "reference": "Amazon mobile: single sticky top bar + hamburger menu drawer."
    },
    {
        "title": "2. Bottom Navigation Bar (NEW)",
        "problem": "All navigation requires scrolling back to the top navbar. "
                   "Thumb-reachable navigation is absent.",
        "fix": "Fixed bottom bar: Home · Materials · Analyzer · Pros · Profile. "
               "Active state highlighted in brand pink. Body gets bottom padding equal to bar height "
               "so content is never hidden behind it.",
        "reference": "Amazon/Myntra/Nykaa: all use bottom nav as primary mobile navigation."
    },
    {
        "title": "3. Product/Material Cards — vertical → Myntra horizontal list",
        "problem": "Catalog grid renders 2 cards per row. Each card is ~300px tall "
                   "(full image + content stacked). User sees only 1.5 cards above fold.",
        "fix": "Grid collapses to single-column flex list. Each card = 110px image left "
               "+ all content (name, brand, price, climate tags, CTA) right. "
               "Separator is an 8px background gap (same as Myntra). "
               "Climate tags scroll horizontally to prevent wrapping. "
               "Name truncates at 2 lines. 'View Details' becomes an inline text link, "
               "not a full-width button.",
        "reference": "Myntra list view: image 100px left, details right. No card border-radius on list items."
    },
    {
        "title": "4. Category Icon Grid — 2-col → 4-col",
        "problem": "Current 2-column grid shows only 2 category types per row, "
                   "requiring unnecessary scroll to see all options.",
        "fix": "4-column grid with smaller icon (28px) and label (0.7rem). "
               "Users see all 8 category types without scrolling.",
        "reference": "Nykaa mobile: 4-per-row category icons as standard browse entry point."
    },
    {
        "title": "5. Category Pill Tabs — wrapping → horizontal scroll sticky",
        "problem": "Filter pills (All, Cement, Steel, Bricks...) wrap to multiple rows, "
                   "pushing product content down.",
        "fix": "Horizontal scrollable row, no wrap, scroll-snap-type: x mandatory. "
               "Sticky below the search bar so active category is always visible. "
               "Active pill gets brand pink background.",
        "reference": "Myntra/Amazon: sticky horizontal category scroll on catalog page."
    },
    {
        "title": "6. Directory Filter Panel — absolute positioning → static",
        "problem": "Screenshots 15-17 show a purple ghost box overlapping provider cards. "
                   "Root cause: filter panel uses position:absolute or float that doesn't "
                   "clear on mobile, bleeding into the results flow.",
        "fix": "position: static !important, width: 100%, float: none. "
               "Filter panel stacks above results. Apply Filters button goes full width. "
               "Spec tag pills use flex-wrap so they don't overflow.",
        "reference": "Standard mobile pattern: filters above results in single-column layout."
    },
    {
        "title": "7. Provider Cards (Contractor/Designer) — compact list",
        "problem": "Cards show full banner height (~120px), large avatar, "
                   "AND spec tag chips — all consuming excess vertical space.",
        "fix": "Banner reduced to 48px. Avatar 52px, pulled up 26px to overlap banner "
               "(standard profile card pattern). Spec tags hidden on mobile. "
               "View Profile button full-width. Card separator uses 8px background gap.",
        "reference": "LinkedIn mobile / Nykaa expert cards: compact avatar + key stats only."
    },
    {
        "title": "8. Dashboard Cards — grid tiles → icon-left list rows",
        "problem": "Dashboard info cards (View Profile, Saved Materials, etc.) "
                   "render as wide square tiles that feel oversized on mobile.",
        "fix": "Flex row: 44px icon square left + h3 title + p subtitle right. "
               "Separated by 6px background gaps. No border-radius (flat list pattern). "
               "Stat cards (7 items, 1 inquiry) get a 4px left accent border.",
        "reference": "Amazon/Nykaa account page: flat list rows with leading icon."
    },
    {
        "title": "9. Sticky Search Bar",
        "problem": "Search bar is not sticky — scrolling past the hero loses access to search.",
        "fix": "Search bar gets position: sticky, top: 56px (below navbar), z-index: 190. "
               "Always accessible without scrolling back to top.",
        "reference": "Amazon mobile: search bar pinned to top on all pages."
    },
    {
        "title": "10. Global overflow-x fix",
        "problem": "Any element wider than the viewport (long text, un-clamped grids) "
                   "causes a horizontal scrollbar on iOS/Android.",
        "fix": "body { overflow-x: hidden }, all containers { max-width: 100vw }. "
               "box-sizing: border-box on all elements so padding doesn't add to width.",
        "reference": "Universal mobile best practice."
    },
]

def main():
    print("\n🔍  OurHome Mobile Redesign Audit")
    print("=" * 52)

    # ── Read CSS files ──────────────────────────────────────────────────────
    css_analyses = {}
    if CSS_DIR.exists():
        for f in sorted(CSS_DIR.glob("*.css")):
            if "mobile_redesign" in f.name:
                continue  # skip our own output
            a = analyse_css_file(f)
            css_analyses[str(f)] = a
            if a:
                mob = len(a['existing_mobile'])
                print(f"  📄 {f.name:30s} {a['size']:6d} bytes   "
                      f"{'⚠ no mobile rules' if mob == 0 else f'{mob} @media block(s)'}")
    else:
        print(f"  ⚠  {CSS_DIR} not found — run from project root.")

    # ── Read templates ──────────────────────────────────────────────────────
    template_analyses = {}
    if TEMPLATES_DIR.exists():
        for f in sorted(TEMPLATES_DIR.rglob("*.html")):
            a = analyse_template(f)
            template_analyses[str(f)] = a
        print(f"\n  🗂  {len(template_analyses)} templates scanned")
    else:
        print(f"  ⚠  {TEMPLATES_DIR} not found — templates not scanned.")

    # ── Generate outputs ────────────────────────────────────────────────────
    print("\n  ✍  Generating outputs …")

    css_text  = generate_mobile_css(css_analyses, template_analyses)
    report    = generate_report(css_analyses, template_analyses, CHANGES_SUMMARY)
    patch     = generate_patch_html()

    OUTPUT_CSS.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_CSS.write_text(css_text, encoding="utf-8")
    OUTPUT_REPORT.write_text(report, encoding="utf-8")
    OUTPUT_PATCH.write_text(patch, encoding="utf-8")

    print(f"  ✅  {OUTPUT_CSS}      ← drop-in mobile CSS")
    print(f"  ✅  {OUTPUT_REPORT}  ← explained change log")
    print(f"  ✅  {OUTPUT_PATCH}   ← base.html snippet (bottom nav + JS)")

    print()
    print("=" * 52)
    print("  Next steps:")
    print(f"  1. Add to base.html <head>:")
    print(f"       {{% load static %}}")
    print(f'       <link rel="stylesheet" href="{{% static \'css/mobile_redesign.css\' %}}">') 
    print(f"  2. Copy bottom nav + JS from mobile_redesign_patch.html into base.html")
    print(f"  3. python manage.py collectstatic --noinput")
    print(f"  4. Deploy and test at 375px viewport\n")
    print(f"  Full change explanations: {OUTPUT_REPORT}\n")

if __name__ == "__main__":
    main()
