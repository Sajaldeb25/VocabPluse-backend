from django.conf import settings
from django.db import models


class AIUsage(models.Model):
    """One row per (identity, word) AI explanation unlock; enforces limits.

    Identity is either a logged-in user or an anonymous session key.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_usages",
        null=True,
        blank=True,
    )
    session_key = models.CharField(max_length=80, blank=True, db_index=True)
    word = models.ForeignKey(
        "vocabulary.Word", on_delete=models.CASCADE, related_name="ai_usages"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "word"],
                name="unique_user_word_usage",
                condition=models.Q(user__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["session_key", "word"],
                name="unique_session_word_usage",
                condition=models.Q(user__isnull=True),
            ),
        ]

    def __str__(self):
        who = self.user.email if self.user else f"session:{self.session_key}"
        return f"{who} -> {self.word.text}"
