# OurHome Mobile Redesign Report
*Generated: 2026-03-18 03:24*

## Reference Design Patterns
| Platform | Key Mobile Patterns Used |
|----------|--------------------------|
| **Amazon** | Sticky search, horizontal scroll carousels, compact list cards, bottom nav |
| **Myntra** | Horizontal list cards (image left), sticky category pills, slide-up filter drawer |
| **Nykaa** | 4-col category icons, bottom nav, compact provider rows, scroll-snap carousels |

---

## Files Analysed

### CSS Files

### Templates

---

## What Changed & Why

### 1. Navbar — 2-row collapse → hamburger drawer
**Problem:** Screenshots show nav links and Sign In button wrapping to a second row, consuming ~25% of screen height before any content.

**Fix:** Nav links hidden by default. Single-row sticky bar: logo + hamburger + avatar. Links appear in a full-screen overlay drawer on hamburger tap. Overlay closes on outside click or nav link click. Body scroll locked when open.

**Reference:** Amazon mobile: single sticky top bar + hamburger menu drawer.

### 2. Bottom Navigation Bar (NEW)
**Problem:** All navigation requires scrolling back to the top navbar. Thumb-reachable navigation is absent.

**Fix:** Fixed bottom bar: Home · Materials · Analyzer · Pros · Profile. Active state highlighted in brand pink. Body gets bottom padding equal to bar height so content is never hidden behind it.

**Reference:** Amazon/Myntra/Nykaa: all use bottom nav as primary mobile navigation.

### 3. Product/Material Cards — vertical → Myntra horizontal list
**Problem:** Catalog grid renders 2 cards per row. Each card is ~300px tall (full image + content stacked). User sees only 1.5 cards above fold.

**Fix:** Grid collapses to single-column flex list. Each card = 110px image left + all content (name, brand, price, climate tags, CTA) right. Separator is an 8px background gap (same as Myntra). Climate tags scroll horizontally to prevent wrapping. Name truncates at 2 lines. 'View Details' becomes an inline text link, not a full-width button.

**Reference:** Myntra list view: image 100px left, details right. No card border-radius on list items.

### 4. Category Icon Grid — 2-col → 4-col
**Problem:** Current 2-column grid shows only 2 category types per row, requiring unnecessary scroll to see all options.

**Fix:** 4-column grid with smaller icon (28px) and label (0.7rem). Users see all 8 category types without scrolling.

**Reference:** Nykaa mobile: 4-per-row category icons as standard browse entry point.

### 5. Category Pill Tabs — wrapping → horizontal scroll sticky
**Problem:** Filter pills (All, Cement, Steel, Bricks...) wrap to multiple rows, pushing product content down.

**Fix:** Horizontal scrollable row, no wrap, scroll-snap-type: x mandatory. Sticky below the search bar so active category is always visible. Active pill gets brand pink background.

**Reference:** Myntra/Amazon: sticky horizontal category scroll on catalog page.

### 6. Directory Filter Panel — absolute positioning → static
**Problem:** Screenshots 15-17 show a purple ghost box overlapping provider cards. Root cause: filter panel uses position:absolute or float that doesn't clear on mobile, bleeding into the results flow.

**Fix:** position: static !important, width: 100%, float: none. Filter panel stacks above results. Apply Filters button goes full width. Spec tag pills use flex-wrap so they don't overflow.

**Reference:** Standard mobile pattern: filters above results in single-column layout.

### 7. Provider Cards (Contractor/Designer) — compact list
**Problem:** Cards show full banner height (~120px), large avatar, AND spec tag chips — all consuming excess vertical space.

**Fix:** Banner reduced to 48px. Avatar 52px, pulled up 26px to overlap banner (standard profile card pattern). Spec tags hidden on mobile. View Profile button full-width. Card separator uses 8px background gap.

**Reference:** LinkedIn mobile / Nykaa expert cards: compact avatar + key stats only.

### 8. Dashboard Cards — grid tiles → icon-left list rows
**Problem:** Dashboard info cards (View Profile, Saved Materials, etc.) render as wide square tiles that feel oversized on mobile.

**Fix:** Flex row: 44px icon square left + h3 title + p subtitle right. Separated by 6px background gaps. No border-radius (flat list pattern). Stat cards (7 items, 1 inquiry) get a 4px left accent border.

**Reference:** Amazon/Nykaa account page: flat list rows with leading icon.

### 9. Sticky Search Bar
**Problem:** Search bar is not sticky — scrolling past the hero loses access to search.

**Fix:** Search bar gets position: sticky, top: 56px (below navbar), z-index: 190. Always accessible without scrolling back to top.

**Reference:** Amazon mobile: search bar pinned to top on all pages.

### 10. Global overflow-x fix
**Problem:** Any element wider than the viewport (long text, un-clamped grids) causes a horizontal scrollbar on iOS/Android.

**Fix:** body { overflow-x: hidden }, all containers { max-width: 100vw }. box-sizing: border-box on all elements so padding doesn't add to width.

**Reference:** Universal mobile best practice.

---

## How to Apply

```bash
# 1. The CSS is already written to static/css/mobile_redesign.css
# 2. Add to your base template <head> AFTER all other CSS:
#    <link rel="stylesheet" href="{% static 'css/mobile_redesign.css' %}">
# 3. Add the bottom nav HTML + hamburger JS from mobile_redesign_patch.html
# 4. Collect static and redeploy:
python manage.py collectstatic --noinput
```

## CSS File Map

```
mobile_redesign.css sections:
  :root        — design tokens (brand colours, spacing, nav heights)
  §1           — global resets (box-sizing, overflow-x)
  §2           — top navbar (sticky, hamburger, drawer)
  §3           — sticky search bar
  §4           — bottom navigation bar (NEW — requires patch.html)
  §5           — hero section
  §6           — climate zone 2-col cards
  §7           — category icon 4-col grid
  §8           — product/material cards (Myntra horizontal list)
  §9           — category pill tabs (horizontal scroll, sticky)
  §10          — filter bar (stacked vertical)
  §11          — directory cards + filter overlap fix
  §12          — dashboard cards + stat cards + scroll carousels
  §13          — section headers + view-all links
  §14          — Material Analyzer CTA banner
  §15          — utility spacing + footer padding
```
