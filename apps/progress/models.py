from django.conf import settings
from django.db import models


class UserProgress(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("learning", "Learning"),
        ("known", "Known"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="progress"
    )
    word = models.ForeignKey(
        "vocabulary.Word", on_delete=models.CASCADE, related_name="progress"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    times_seen = models.PositiveIntegerField(default=0)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "word")
        ordering = ("-last_seen",)
        verbose_name_plural = "User progress"

    def __str__(self):
        return f"{self.user.email} / {self.word.text} [{self.status}]"
