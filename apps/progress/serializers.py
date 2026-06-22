from rest_framework import serializers

from .models import UserProgress


class UserProgressSerializer(serializers.ModelSerializer):
    word_text = serializers.CharField(source="word.text", read_only=True)

    class Meta:
        model = UserProgress
        fields = ("id", "word", "word_text", "status", "times_seen", "last_seen")
        read_only_fields = ("id", "word_text", "times_seen", "last_seen")
