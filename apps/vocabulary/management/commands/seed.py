"""Seed demo data: categories, sets, words, demo words, exam questions, a plan."""
from django.core.management.base import BaseCommand

from apps.core.models import SiteSetting
from apps.subscriptions.models import Plan
from apps.vocabulary.models import (
    Category,
    ExampleQuestion,
    Word,
    WordSet,
)

SAMPLE_WORDS = {
    "easy": [
        ("abate", "verb", "to become less intense or widespread", "The storm finally abated."),
        ("benevolent", "adj", "well meaning and kindly", "A benevolent smile."),
        ("candid", "adj", "truthful and straightforward", "Her candid reply surprised us."),
        ("diligent", "adj", "showing careful and persistent effort", "A diligent student."),
    ],
    "medium": [
        ("ephemeral", "adj", "lasting for a very short time", "Fashions are ephemeral."),
        ("gregarious", "adj", "fond of company; sociable", "A gregarious host."),
        ("hackneyed", "adj", "overused and unoriginal", "A hackneyed phrase."),
    ],
    "hard": [
        ("inchoate", "adj", "just begun and not fully formed", "Inchoate ideas."),
        ("laconic", "adj", "using very few words", "A laconic reply."),
    ],
    "advanced": [
        ("perspicacious", "adj", "having keen insight", "A perspicacious analyst."),
        ("recalcitrant", "adj", "stubbornly resistant to authority", "A recalcitrant pupil."),
    ],
}


class Command(BaseCommand):
    help = "Seed the database with demo categories, words, a plan and settings."

    def handle(self, *args, **options):
        SiteSetting.load()

        Plan.objects.get_or_create(
            slug="pro-monthly",
            defaults={
                "name": "Pro Monthly",
                "price": "299.00",
                "currency": "BDT",
                "duration_days": 30,
                "description": "Unlimited AI explanations, all levels, exam questions.",
            },
        )

        demo_assigned = 0
        for cat_name, cat_slug in [("GRE words", "gre"), ("Other words", "other")]:
            category, _ = Category.objects.get_or_create(
                slug=cat_slug, defaults={"name": cat_name}
            )
            for level, words in SAMPLE_WORDS.items():
                word_set, _ = WordSet.objects.get_or_create(
                    category=category,
                    level=level,
                    order=1,
                    defaults={"title": f"{level.title()} Set 1"},
                )
                for text, pos, definition, example in words:
                    word, created = Word.objects.get_or_create(
                        word_set=word_set,
                        text=text,
                        defaults={
                            "part_of_speech": pos,
                            "simple_definition": definition,
                            "example_sentence": example,
                            "level": level,
                        },
                    )
                    # Mark first 3 easy words across the catalog as demo words.
                    if level == "easy" and demo_assigned < 3 and not word.is_demo:
                        word.is_demo = True
                        word.save(update_fields=["is_demo"])
                        demo_assigned += 1
                    if created:
                        ExampleQuestion.objects.create(
                            word=word,
                            question_text=f"Choose the meaning closest to '{text}'.",
                            options=[definition, "an unrelated meaning", "another option"],
                            answer=definition,
                            source="gre" if cat_slug == "gre" else "bd_govt",
                            year=2023,
                        )

        self.stdout.write(self.style.SUCCESS("Seed complete."))
