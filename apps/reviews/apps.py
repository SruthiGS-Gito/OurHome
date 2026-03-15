from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    name = 'apps.reviews'

    def ready(self):
        # Importing signals here registers the @receiver decorators.
        # Django calls ready() once at startup — this is the standard pattern.
        import apps.reviews.signals  # noqa: F401
