from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    has_active_subscription = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "has_active_subscription")
        read_only_fields = fields
