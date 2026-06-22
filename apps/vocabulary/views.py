import random

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.ai.models import AIUsage
from apps.ai.services import generate_explanation
from apps.core.access import ensure_session_key, get_access

from .models import AIExplanation, Category, Word, WordSet
from .serializers import (
    CategorySerializer,
    ExampleQuestionSerializer,
    WordCardSerializer,
    WordDefineSerializer,
    WordSetSerializer,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def category_list(request):
    categories = Category.objects.all()
    return Response(CategorySerializer(categories, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def wordset_list(request):
    access = get_access(request)
    qs = WordSet.objects.select_related("category")

    category = request.query_params.get("category")
    level = request.query_params.get("level")
    if category:
        qs = qs.filter(category__slug=category)
    if level:
        qs = qs.filter(level=level)

    serializer = WordSetSerializer(
        qs, many=True, context={"allowed_levels": access["allowed_levels"]}
    )
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def wordset_cards(request, pk):
    """Return shuffled word cards for a set the user is allowed to browse."""
    access = get_access(request)
    word_set = get_object_or_404(WordSet, pk=pk)
    if word_set.level not in access["allowed_levels"]:
        return Response(
            {"detail": "This level requires a subscription."},
            status=status.HTTP_403_FORBIDDEN,
        )
    words = list(word_set.words.all())
    random.shuffle(words)
    return Response(WordCardSerializer(words, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def word_define(request, pk):
    access = get_access(request)
    word = get_object_or_404(Word, pk=pk)
    if word.level not in access["allowed_levels"]:
        return Response(
            {"detail": "This level requires a subscription."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return Response(WordDefineSerializer(word).data)


def _usage_filter(access, request, word):
    if access["is_authenticated"]:
        return {"user": access["user"], "word": word}
    return {"session_key": ensure_session_key(request), "word": word}


def _usage_count(access, request):
    if access["is_authenticated"]:
        return AIUsage.objects.filter(user=access["user"]).count()
    return AIUsage.objects.filter(
        session_key=ensure_session_key(request), user__isnull=True
    ).count()


@api_view(["POST"])
@permission_classes([AllowAny])
def word_explain(request, pk):
    """Return an AI explanation, enforcing per-identity usage limits.

    - Subscribers: unlimited.
    - Anonymous: only demo words, capped at anon_ai_limit distinct words.
    - Free logged-in: capped at free_ai_limit distinct words.
    Already-unlocked words return the cached explanation without re-counting.
    """
    access = get_access(request)
    word = get_object_or_404(Word, pk=pk)

    if word.level not in access["allowed_levels"]:
        return Response(
            {"detail": "This level requires a subscription."},
            status=status.HTTP_403_FORBIDDEN,
        )

    usage_filter = _usage_filter(access, request, word)
    already_unlocked = AIUsage.objects.filter(**usage_filter).exists()

    cached = AIExplanation.objects.filter(word=word).first()
    if already_unlocked and cached:
        return Response({"content": cached.content, "cached": True})

    if not already_unlocked:
        # Anonymous users may only unlock demo words.
        if not access["is_authenticated"] and not word.is_demo:
            return Response(
                {
                    "detail": "Log in to unlock AI explanations for this word.",
                    "reason": "login_required",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        limit = access["ai_limit"]
        if limit is not None and _usage_count(access, request) >= limit:
            return Response(
                {
                    "detail": "AI explanation limit reached. Subscribe for unlimited access.",
                    "reason": "limit_reached",
                },
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

    if cached:
        content = cached.content
    else:
        content = generate_explanation(word)
        cached = AIExplanation.objects.create(
            word=word,
            content=content,
            model_name=request.data.get("model", ""),
        )

    if not already_unlocked:
        AIUsage.objects.get_or_create(**usage_filter)

    return Response({"content": content, "cached": False})


@api_view(["GET"])
@permission_classes([AllowAny])
def word_questions(request, pk):
    """Past exam questions for a word; subscribers only."""
    access = get_access(request)
    word = get_object_or_404(Word, pk=pk)
    if not access["is_subscriber"]:
        return Response(
            {
                "detail": "Example questions require an active subscription.",
                "reason": "subscription_required",
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    questions = word.example_questions.all()
    return Response(ExampleQuestionSerializer(questions, many=True).data)
