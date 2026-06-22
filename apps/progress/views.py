from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.vocabulary.models import Word

from .models import UserProgress
from .serializers import UserProgressSerializer


class ProgressView(APIView):
    """List the user's progress, or record/update progress for a word."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = request.user.progress.select_related("word")
        return Response(UserProgressSerializer(qs, many=True).data)

    def post(self, request):
        word = get_object_or_404(Word, pk=request.data.get("word"))
        new_status = request.data.get("status")

        progress, _ = UserProgress.objects.get_or_create(
            user=request.user, word=word
        )
        progress.times_seen += 1
        if new_status in dict(UserProgress.STATUS_CHOICES):
            progress.status = new_status
        progress.save()
        return Response(
            UserProgressSerializer(progress).data, status=status.HTTP_200_OK
        )
