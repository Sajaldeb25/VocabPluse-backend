from rest_framework import serializers

from .models import Category, ExampleQuestion, Word, WordSet


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "order")


class WordSetSerializer(serializers.ModelSerializer):
    word_count = serializers.IntegerField(source="words.count", read_only=True)
    locked = serializers.SerializerMethodField()

    class Meta:
        model = WordSet
        fields = ("id", "category", "level", "title", "order", "word_count", "locked")

    def get_locked(self, obj):
        allowed = self.context.get("allowed_levels", set())
        return obj.level not in allowed


class WordCardSerializer(serializers.ModelSerializer):
    """Minimal card payload (no definition until 'Define' is pressed)."""

    class Meta:
        model = Word
        fields = ("id", "text", "part_of_speech", "level", "is_demo")


class WordDefineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = (
            "id", "text", "part_of_speech",
            "simple_definition", "example_sentence", "level",
        )


class ExampleQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExampleQuestion
        fields = ("id", "question_text", "options", "answer", "source", "year")
