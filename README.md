# Our Kitchen

A private, mobile-first household recipe application. The current foundation includes the approved React interface plus a FastAPI API, one shared household workspace, persistent recipes, Meals on Deck, grocery snapshots, Pantry Staples, cooking history, and validated recipe-photo uploads.

## Stack

- React + TypeScript + Vite for the responsive interface
- FastAPI and Pydantic for the JSON API
- SQLAlchemy 2 and SQLite with WAL, foreign keys, and a busy timeout
- Alembic for database migrations
- Cloudflare Access JWT verification for future production access
- Filesystem image storage with database metadata
- Vitest/Testing Library and Pytest/HTTPX for tests

## Prerequisites

- Node.js 20+ and npm 10+
- Python 3.12+
- Python virtual-environment support (`python3.12-venv` on Ubuntu)

## Initial setup

```bash
npm install
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cp .env.example .env
```

The example explicitly sets `OUR_KITCHEN_AUTH_MODE=local`, which bypasses identity verification only for local development. Do not commit `.env`. To enable optional AI features locally, add `OPENAI_API_KEY` to that untracked file. `OPENAI_MODEL` defaults to the low-cost, text-and-image capable `gpt-6-luna`; model prices are centralized in `backend/app/ai.py` and must be updated when the model changes.

Apply the schema and initialize the shared household:

```bash
python -m alembic -c backend/alembic.ini upgrade head
python -m backend.app.bootstrap
```

## Run locally

Start the API from the repository root:

```bash
source .venv/bin/activate
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, start Vite:

```bash
npm run dev
```

Open `http://localhost:5173`; no application login is required in explicit local mode. Vite proxies `/api` and `/media` to FastAPI. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Tests and production build

```bash
npm test
npm run build
source .venv/bin/activate
pytest backend/tests
```

To verify migrations against a disposable database, set `OUR_KITCHEN_DATABASE_URL` to a temporary SQLite path before running the Alembic command.

## Structure

```text
src/
  api.ts             Typed API boundary and JSON-to-UI mapping
  components/        Shared navigation, cards, icons, and search
  screens/           Responsive application screens
  sample-recipes.ts  Temporary data for unconnected later-phase features
backend/
  app/               FastAPI application, models, schemas, and route modules
  alembic/           Versioned database migrations
  tests/             Workspace, recipe, deck, grocery, pantry, and upload tests
```

Runtime data defaults to `data/our-kitchen.sqlite3` and `data/media/`. Both paths are ignored by Git and can later be mounted as persistent Docker volumes. Change them with `OUR_KITCHEN_DATABASE_URL` and `OUR_KITCHEN_MEDIA_ROOT`.

## Current API scope

- Recipe CRUD plus search/status/cuisine/tag/time filters
- Reusable add/edit form, confirmed deletion, and “Made this” cooking history
- JPEG, PNG, and WebP cover-photo uploads with size and content validation
- Shared Pantry Staples list/create/delete operations
- Persistent Meals on Deck with per-meal servings, completion history, removal, and completed-item clearing
- Explicit grocery preview/apply workflow with serving scaling, compatible-unit consolidation, pantry exclusions, and persistent manual/checkoff edits
- Persistent Recipe Inbox for URLs and multi-page image uploads, with review, retry, duplicate warnings, deletion, and source preservation
- SSRF-aware schema.org/JSON-LD website extraction plus public YouTube metadata fallback; incomplete imports remain manual drafts
- Explicit OpenAI Responses API fallback for website/video imports and multi-image cookbook or handwritten transcription; every result goes through review
- Saved-library-first What Can I Make and Help Me Pick, with separately labeled, unsaved AI ideas
- Contextual, non-destructive cooking assistance in Recipe Detail and Cook Mode
- Household AI usage display with a $10 monthly application budget, $8 warning, and concurrency-safe request reservations
- Household scoping on every recipe, image, pantry, deck, and grocery query

The Recipe Library, Recipe Detail, Household Settings/Pantry Staples, Meals on Deck, Grocery List, Recipe Inbox, What Can I Make, Help Me Pick, and A Little Inspiration cooking history use the API. Ordinary library matching and planning remain available without an OpenAI key.

AI cost figures are estimates derived from reported token usage and the configured pricing table. Failed requests or responses without usage data are conservatively charged at their reservation amount. Reservations reduce concurrent overspend risk, but an application-level tracker cannot guarantee an exact hard cap on provider billing; set provider-side project limits and alerts as an additional safeguard.

## Access and security

- `OUR_KITCHEN_AUTH_MODE=local` must be set explicitly for the credential-free local preview.
- The default mode is `cloudflare`; it rejects API requests unless the `Cf-Access-Jwt-Assertion` is verified against the configured Cloudflare Access issuer, signing keys, and audience.
- Production configuration requires `OUR_KITCHEN_CLOUDFLARE_ACCESS_TEAM_DOMAIN` and `OUR_KITCHEN_CLOUDFLARE_ACCESS_AUDIENCE`. Missing or invalid verification fails closed at the API boundary.
- An email header by itself is never trusted. Cloudflare Tunnel and Access are not configured or deployed in this phase.
- Uploaded files are renamed, type/size checked, decoded as images, and stored outside the frontend bundle.

## Next backend sequence

1. Add optional persistence for recent discovery prompts if the household finds it useful.
2. Validate model pricing before each model change and add provider-side project limits.
3. Add rate limiting, Docker, backups, and secure remote access before deployment.
