"""Gemini AI service with a safe offline fallback.

When GEMINI_API_KEY (and the google-generativeai package) is available the
real model is called; otherwise a deterministic stub is returned so the app
and tests work without network access or credentials.
"""
from django.conf import settings


def _build_prompt(word):
    return (
        "You are an English vocabulary tutor. Explain the word "
        f'"{word.text}" for a learner. Include: a clear meaning, '
        "nuances/usage, 2 example sentences, common synonyms and antonyms, "
        "and a memory tip. Keep it concise and well structured."
    )


def _stub_response(word):
    pos = f" ({word.part_of_speech})" if word.part_of_speech else ""
    return (
        f"AI explanation for '{word.text}'{pos}:\n\n"
        f"Meaning: {word.simple_definition}\n\n"
        f"Example: {word.example_sentence or 'See the definition above.'}\n\n"
        "Memory tip: connect this word to a vivid mental image to recall it.\n\n"
        "(Configure GEMINI_API_KEY to get richer AI-generated explanations.)"
    )


def generate_explanation(word):
    """Return an AI explanation string for the given word."""
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        return _stub_response(word)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content(_build_prompt(word))
        text = getattr(response, "text", "") or ""
        return text.strip() or _stub_response(word)
    except Exception:  # noqa: BLE001 - never break the request on AI failure
        return _stub_response(word)
