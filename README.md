# Our Kitchen

A mobile-first UI foundation for a private household recipe collection. This phase uses sample data only; it intentionally excludes authentication, database persistence, imports, AI, deployment, and remote access.

## Stack

- React + TypeScript for interactive, typed screens
- Vite for local development and builds
- Plain CSS for the light sage-and-cream design system
- Vitest + Testing Library for unit and interaction tests

This is the smallest maintainable form of the proposed React/FastAPI architecture for this UI-only milestone. Sample records sit behind `src/data.ts`, so an API repository can replace them later without rewriting screens.

## Local development

Requires Node.js 20+ and npm 10+.

```bash
npm install
npm run dev
```

Open the URL Vite prints, normally `http://localhost:5173`.

## Tests and production build

```bash
npm test
npm run build
npm run preview
```

The build runs strict TypeScript checks before creating `dist/`.

## Structure

```text
src/
  components/       Shared navigation, cards, icons, and search
  screens/          Home, library, recipe/cook, deck, groceries, inbox
  utils/            Deterministic display helpers
  types.ts          Backend-aligned domain types
  sample-recipes.ts Sample UI records
  data.ts           Replaceable data boundary
```

## Recommended backend sequence

1. Add FastAPI routes, SQLite WAL/busy timeout, SQLAlchemy, and Alembic.
2. Add household authentication and authorization before remote access.
3. Replace sample data with an API repository and implement recipe CRUD.
4. Persist Meals on Deck and the grocery snapshot/diff workflow.
5. Add deterministic URL extraction and reviewable Inbox jobs.
6. Add Docker, backups, and secure remote access after local security tests.
