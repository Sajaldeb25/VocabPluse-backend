# VocabPluse API (backend)

REST API for [vocabpluse.com](https://vocabpluse.com) — flashcard-based English vocabulary learning with AI explanations, past-exam questions, progress tracking, Google login, and subscription payments. Content is managed through the **Django admin**.

This repository is the **backend only**. The Vue 3 frontend lives in a separate repository and consumes this API.

> The full backend architecture and deployment plan lives in [PLAN.md](PLAN.md).

---

## Features

- Vocabulary catalog: **GRE words** and **Other words**, each with four levels (Easy, Medium, Hard, Advanced).
- **Word sets** (~30 words each) served as shuffled flashcard decks.
- Per-word actions:
  1. **Define** — simple definition + example (free for browsable words).
  2. **Explanation with AI** — Gemini-generated explanation, cached per word.
  3. **Example Questions** — past GRE / Bangladesh govt exam questions (subscribers only).
- **Access tiers** (enforced server-side)

  | User | Browse | Define | AI explanation | Example questions | Progress |
  |------|--------|--------|----------------|-------------------|----------|
  | Anonymous | Easy + Medium | Yes | 3 demo words | No | No |
  | Logged-in (free) | Easy + Medium | Yes | 5 total | No | Yes |
  | Subscriber | All levels | Yes | Unlimited | Yes | Yes |

  Limits (`3` / `5`) and `words_per_set` are configurable in the Django admin.

---

## Tech stack

- **Framework:** Django 5, Django REST Framework
- **Auth:** Google ID-token login → JWT (SimpleJWT)
- **AI:** Google Gemini (`google-generativeai`) with a safe offline fallback
- **Payments:** SSLCommerz (sandbox-first; mock flow when no credentials)
- **Database:** SQLite by default; PostgreSQL via `DATABASE_URL`
- **Config:** `django-environ`, `django-cors-headers`

---

## Project layout

```
.
  config/        settings, urls, wsgi/asgi
  apps/
    core/        site settings, shared utilities
    accounts/    custom user, Google auth, JWT
    vocabulary/  categories, word sets, words, questions
    ai/          Gemini service, usage limits, caching
    subscriptions/  plans, payments, SSLCommerz
    progress/    user progress tracking
  tests/         automated API tests
  manage.py
  requirements.txt
```

---

## Quick start

Prerequisites: **Python 3.12+** (PostgreSQL optional).

### First-time setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env            # optional; defaults work out of the box

python manage.py migrate
python manage.py seed           # demo categories, words, a plan, settings
python manage.py createsuperuser
python manage.py runserver
```

### Daily development

```bash
source .venv/bin/activate
pip install -r requirements.txt   # after dependency changes
python manage.py runserver
```

To deactivate the virtual environment:

```bash
deactivate
```

- API: <http://localhost:8000/api/>
- Admin: <http://localhost:8000/admin/>

Without API keys the app still runs: AI returns a built-in fallback explanation, and checkout uses a mock payment flow so gated features can be tested locally.

---

## Configuration (environment variables)

Create a `.env` file in the project root (see `.env.example` when available).

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | dev key | Django secret (set in production) |
| `DEBUG` | `False` | Debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hosts |
| `SITE_URL` | `http://localhost:8000` | Base URL for payment callbacks |
| `DATABASE_URL` | SQLite | e.g. `postgres://user:pass@host:5432/vocabpluse` |
| `CORS_ALLOWED_ORIGINS` | localhost:5173 | Frontend origins (comma-separated) |
| `GOOGLE_OAUTH_CLIENT_ID` | empty | Google OAuth client id |
| `GEMINI_API_KEY` | empty | Enables real Gemini (else fallback) |
| `GEMINI_MODEL` | `gemini-2.5-flash-lite` | Gemini model name |
| `SSLCOMMERZ_STORE_ID` / `SSLCOMMERZ_STORE_PASSWORD` | empty | Payment credentials |
| `SSLCOMMERZ_SANDBOX` | `True` | Use sandbox gateway |

To use real Gemini: `pip install google-generativeai` and set `GEMINI_API_KEY`.

To use PostgreSQL: `pip install psycopg2-binary` and set `DATABASE_URL`.

---

## API overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/health/` | — | Health check |
| POST | `/api/auth/google/` | — | Exchange Google ID token for JWT |
| POST | `/api/auth/refresh/` | — | Refresh access token |
| GET | `/api/auth/user/` | JWT | Current user |
| GET | `/api/categories/` | — | List categories |
| GET | `/api/wordsets/?category=&level=` | — | List sets (locked flag by access) |
| GET | `/api/wordsets/{id}/cards/` | — | Shuffled cards (level-gated) |
| GET | `/api/words/{id}/define/` | — | Definition (level-gated) |
| POST | `/api/words/{id}/explain/` | — | AI explanation (cached + limited) |
| GET | `/api/words/{id}/questions/` | — | Exam questions (subscribers only) |
| GET/POST | `/api/progress/` | JWT | View / record progress |
| GET | `/api/plans/` | — | Subscription plans |
| POST | `/api/subscriptions/checkout/` | JWT | Start checkout |
| POST/GET | `/api/payments/callback/{outcome}/` | — | Gateway callback |

---

## Running tests

```bash
source .venv/bin/activate
python manage.py test
```

Tests cover access gating, AI usage limits + caching, subscription/payment activation, Google login, and progress tracking. They run on an in-memory SQLite database and need no network or API keys.

---

## Managing content (Django admin)

Log in at `/admin/` and use:

- **Categories** / **Word sets** / **Words** — build the catalog (add words inline under a set; mark a few as **demo** so anonymous users can try AI).
- **Words → Example questions / AI explanation** — inline editing per word.
- **Plans** — create/price subscription plans.
- **Subscriptions / Payments** — view and manage user subscriptions.
- **Site settings** — tune AI limits and words-per-set.

---

## Deployment summary

Recommended: Gunicorn behind Nginx on a VPS, with PostgreSQL and Cloudflare for DNS/CDN/SSL. The frontend SPA is built and served separately (or from the same Nginx host as static files).

1. Set production env: `DEBUG=False`, `SECRET_KEY`, `ALLOWED_HOSTS`, `SITE_URL`, `DATABASE_URL`, `CORS_ALLOWED_ORIGINS`.
2. `pip install -r requirements.txt google-generativeai` (PostgreSQL driver included in requirements).
3. `python manage.py migrate && python manage.py collectstatic`
4. Serve via `gunicorn config.wsgi:application` behind Nginx.
5. Point Cloudflare DNS to the server; enable SSL (Full strict).
6. Set Google OAuth authorized origins and SSLCommerz callback URLs to the production domain.

See [PLAN.md](PLAN.md) for module breakdown, deployment topology, and cost estimates.

---

## Troubleshooting

### `pip install` fails on `google-generativeai`

Optional. The app runs without it (AI uses a built-in fallback). Install only when enabling real Gemini.

### Port already in use

Default port is `8000`. Use `python manage.py runserver 8001` to change it.

### CORS errors from the frontend

Add your frontend origin to `CORS_ALLOWED_ORIGINS` in `.env`, e.g. `http://localhost:5173`.
