from django.db import models

LEVEL_EASY = "easy"
LEVEL_MEDIUM = "medium"
LEVEL_HARD = "hard"
LEVEL_ADVANCED = "advanced"

LEVEL_CHOICES = [
    (LEVEL_EASY, "Easy"),
    (LEVEL_MEDIUM, "Medium"),
    (LEVEL_HARD, "Hard"),
    (LEVEL_ADVANCED, "Advanced"),
]

# Levels any visitor (anonymous or free) may browse.
FREE_LEVELS = {LEVEL_EASY, LEVEL_MEDIUM}


class Category(models.Model):
    """Top-level menu section: GRE words / Other words."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "name")
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class WordSet(models.Model):
    """A chunk/set of words within a category + level (target 30 words)."""

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="word_sets"
    )
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    title = models.CharField(max_length=150)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("category", "level", "order")
        unique_together = ("category", "level", "order")

    def __str__(self):
        return f"{self.category.name} / {self.get_level_display()} / {self.title}"


class Word(models.Model):
    word_set = models.ForeignKey(
        WordSet, on_delete=models.CASCADE, related_name="words"
    )
    text = models.CharField(max_length=100)
    part_of_speech = models.CharField(max_length=50, blank=True)
    simple_definition = models.TextField()
    example_sentence = models.TextField(blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    is_demo = models.BooleanField(
        default=False,
        help_text="Demo words can be AI-explained by anonymous visitors.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("word_set", "text")

    def __str__(self):
        return self.text

    def save(self, *args, **kwargs):
        if not self.level and self.word_set_id:
            self.level = self.word_set.level
        super().save(*args, **kwargs)


class AIExplanation(models.Model):
    """Globally cached AI explanation for a word (generated once)."""

    word = models.OneToOneField(
        Word, on_delete=models.CASCADE, related_name="ai_explanation"
    )
    content = models.TextField()
    model_name = models.CharField(max_length=80, blank=True)
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI explanation for {self.word.text}"


class ExampleQuestion(models.Model):
    """Past exam question (GRE / BD govt) referencing a word."""

    SOURCE_CHOICES = [
        ("gre", "GRE"),
        ("bd_govt", "BD Govt Exam"),
        ("other", "Other"),
    ]

    word = models.ForeignKey(
        Word, on_delete=models.CASCADE, related_name="example_questions"
    )
    question_text = models.TextField()
    options = models.JSONField(blank=True, null=True, help_text="Optional list of MCQ options.")
    answer = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="other")
    year = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"Q for {self.word.text} ({self.get_source_display()})"
