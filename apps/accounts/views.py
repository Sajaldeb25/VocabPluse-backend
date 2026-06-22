from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile, User
from .serializers import UserSerializer


def _tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


def verify_google_id_token(id_token_str):
    """Verify a Google ID token and return its claims.

    Raises ValueError if verification fails. Kept isolated so it can be
    mocked in tests without network access.
    """
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token

    client_id = settings.GOOGLE_OAUTH_CLIENT_ID
    request = google_requests.Request()
    claims = google_id_token.verify_oauth2_token(id_token_str, request, client_id)
    return claims


class GoogleLoginView(APIView):
    """Exchange a Google ID token for VocabPluse JWT tokens.

    Body: {"id_token": "<google id token>"}
    """

    permission_classes = []

    def post(self, request):
        token = request.data.get("id_token")
        if not token:
            return Response(
                {"detail": "id_token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            claims = verify_google_id_token(token)
        except Exception as exc:  # noqa: BLE001 - surface a clean 401
            return Response(
                {"detail": f"Invalid Google token: {exc}"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = claims.get("email")
        if not email:
            return Response(
                {"detail": "Google token has no email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"full_name": claims.get("name", "")},
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.google_sub = claims.get("sub", "")
        if claims.get("picture"):
            profile.avatar_url = claims["picture"]
        profile.save()

        return Response(
            {"user": UserSerializer(user).data, **_tokens_for(user)},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
