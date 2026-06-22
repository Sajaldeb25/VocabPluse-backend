"""Central access-control helpers encoding the VocabPluse access matrix.

Anonymous: browse Easy+Medium; AI only for demo words within anon limit.
Logged-in (free): browse Easy+Medium; AI within free limit; progress tracked.
Subscriber: full catalog; unlimited AI; example questions enabled.
"""
from apps.vocabulary.models import FREE_LEVELS, LEVEL_CHOICES

from .models import SiteSetting

ALL_LEVELS = {value for value, _ in LEVEL_CHOICES}


def ensure_session_key(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def get_access(request):
    """Return an access descriptor for the current request."""
    user = getattr(request, "user", None)
    is_authenticated = bool(user and user.is_authenticated)
    is_subscriber = bool(is_authenticated and user.has_active_subscription)

    if is_subscriber:
        allowed_levels = set(ALL_LEVELS)
    else:
        allowed_levels = set(FREE_LEVELS)

    settings_obj = SiteSetting.load()
    if is_subscriber:
        ai_limit = None  # unlimited
    elif is_authenticated:
        ai_limit = settings_obj.free_ai_limit
    else:
        ai_limit = settings_obj.anon_ai_limit

    return {
        "user": user if is_authenticated else None,
        "is_authenticated": is_authenticated,
        "is_subscriber": is_subscriber,
        "allowed_levels": allowed_levels,
        "ai_limit": ai_limit,
    }
