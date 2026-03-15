"""
apps/reviews/signals.py — Keeps Product aggregate fields in sync with Review data.

WHAT THIS DOES:
  Every time a Review is saved (created, updated) or deleted, these signals fire
  and recompute three fields on the related Product:
    - average_rating   (Decimal, e.g. 4.3)
    - total_reviews    (int, count of approved reviews)
    - rating_breakdown (dict, e.g. {"5": 3, "4": 1, "3": 0, "2": 1, "1": 0})

WHY SIGNALS INSTEAD OF COMPUTING ON EVERY PAGE VIEW:
  Computing average_rating in a template or view requires:
    SELECT AVG(rating) FROM reviews WHERE product_id = 42 AND is_approved = True
  This runs on EVERY product detail page view. With 1,000 daily users × 100 products,
  that's 100,000 extra SQL queries per day — and they get slower as reviews accumulate.

  With signals: the aggregation runs ONCE per review event (rare).
  The product detail view just reads product.average_rating — one fast column lookup.

SIGNAL LIFECYCLE:
  Review created (is_approved=True)  → post_save fires → update Product
  Review updated (is_approved toggled) → post_save fires → update Product
  Review deleted                      → post_delete fires → update Product

IMPORTANT: Signals are registered in ReviewsConfig.ready() in apps.py.
  Without that registration, these receivers never execute.
"""

from django.db.models import Avg
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Review


def _recompute(product):
    """
    Recalculates and saves average_rating, total_reviews, and rating_breakdown
    on the given product using only its approved reviews.

    Uses .update() (a single SQL UPDATE) instead of .save() to avoid:
    - Triggering Product.save() (which regenerates the slug, etc.)
    - Any circular signal issues
    """
    # Import here to avoid circular: reviews → products → reviews
    from apps.products.models import Product

    approved = Review.objects.filter(product=product, is_approved=True)
    total = approved.count()

    if total:
        avg_raw = approved.aggregate(avg=Avg('rating'))['avg']
        avg = round(float(avg_raw), 1)
        breakdown = {str(i): approved.filter(rating=i).count() for i in range(1, 6)}
    else:
        avg = 0.0
        breakdown = {}

    Product.objects.filter(pk=product.pk).update(
        average_rating=avg,
        total_reviews=total,
        rating_breakdown=breakdown,
    )


@receiver(post_save, sender=Review)
def on_review_save(sender, instance, **kwargs):
    _recompute(instance.product)


@receiver(post_delete, sender=Review)
def on_review_delete(sender, instance, **kwargs):
    _recompute(instance.product)
