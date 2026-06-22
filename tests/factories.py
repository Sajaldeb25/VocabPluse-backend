"""Helpers to build test data."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.subscriptions.models import Plan, Subscription
from apps.vocabulary.models import Category, ExampleQuestion, Word, WordSet

User = get_user_model()


def make_user(email="user@example.com"):
    return User.objects.create_user(email=email, password="pass12345")


def make_subscriber(email="sub@example.com"):
    user = make_user(email)
    plan = Plan.objects.create(
        name="Pro", slug=f"pro-{email}", price="299.00", duration_days=30
    )
    sub = Subscription.objects.create(user=user, plan=plan, status="active")
    sub.start_at = timezone.now()
    sub.end_at = timezone.now() + timedelta(days=30)
    sub.save()
    return user


def make_catalog():
    """Create a category with one set per level and a couple of words each."""
    category = Category.objects.create(name="GRE", slug="gre")
    data = {}
    for level in ["easy", "medium", "hard", "advanced"]:
        word_set = WordSet.objects.create(
            category=category, level=level, title=f"{level} set", order=1
        )
        words = []
        for i in range(2):
            words.append(
                Word.objects.create(
                    word_set=word_set,
                    text=f"{level}word{i}",
                    simple_definition=f"definition {level} {i}",
                    example_sentence="An example.",
                    level=level,
                    is_demo=(level == "easy"),
                )
            )
        data[level] = {"set": word_set, "words": words}

    # Add an exam question to an easy word.
    ExampleQuestion.objects.create(
        word=data["easy"]["words"][0],
        question_text="What does it mean?",
        answer="definition easy 0",
        source="gre",
    )
    return data
