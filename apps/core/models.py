from django.core.cache import cache
from django.db import models


class SiteSetting(models.Model):
    """Singleton holding configurable platform limits (managed in admin)."""

    anon_ai_limit = models.PositiveIntegerField(
        default=3,
        help_text="Number of AI explanations an anonymous visitor can unlock.",
    )
    free_ai_limit = models.PositiveIntegerField(
        default=5,
        help_text="Total AI explanations a logged-in free user can unlock.",
    )
    words_per_set = models.PositiveIntegerField(
        default=30,
        help_text="Target number of words per word set / chunk.",
    )

    class Meta:
        verbose_name = "Site setting"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
