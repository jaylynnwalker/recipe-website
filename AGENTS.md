# Codex instructions — Our Kitchen

## Project context
Our Kitchen is a private, mobile-first household recipe website. It will be developed locally and ultimately self-hosted on an existing Ubuntu Server 24.04 machine using Docker Compose.

## Sources of truth
Read these documents before planning or changing functionality or UI:
- `docs/REQUIREMENTS.md` — product behavior and acceptance criteria
- `docs/TECHNICAL_DESIGN.md` — architecture, data model, deployment and security
- `docs/UI_DESIGN.md` — visual design, layouts and interactions

If documents conflict, identify the conflict and ask before making a product decision. Do not silently replace established requirements. Technical options marked *proposed* are not final decisions.

## Product invariants
- Preserve the original **light sage-and-cream** design. Do not switch to a dark/burgundy theme.
- Use **Meals on Deck**, not Dinner Lineup; meals have **no weekday/date assignments** or mandatory weekly reset.
- Recipe detail has separate **Ingredients**, **Instructions**, and **Notes** tabs, plus optional Cook Mode.
- The desktop homepage's recipe suggestions use **compact food-photo cards**, not category icon tiles.
- Use one shared household workspace. Local bypass must be explicit; production API access must verify Cloudflare Access signed identity tokens and fail closed.
- Recipe Inbox must accommodate links and uploaded photos, including multiple cookbook pages; imported recipes require review before saving.
- Grocery lists update on explicit user action with a preview; preserve manual additions and user checkoffs.
- AI is optional/on-demand; ordinary browsing and grocery calculations must not depend on it.

## Engineering guidelines
- Favor the simplest maintainable solution. Avoid extra infrastructure without a demonstrated need.
- Keep secrets out of source control; provide `.env.example` rather than committing credentials.
- Keep persistent user data outside ephemeral containers. Plan for backups of both database and uploaded images.
- Enforce production Cloudflare Access token verification and household scoping at the backend/API boundary, independently of frontend visibility.
- Build responsive, accessible interfaces with readable typography and touch-friendly controls.
- Add or update tests for substantive behavior changes, and run applicable checks before reporting completion.
- Document important architecture decisions and any deliberate deviations from the technical design.

## Workflow
1. Inspect the repository and read the three documents.
2. State the proposed scope and any unresolved technical decisions before major implementation.
3. Implement in small, reviewable increments, starting with the foundation and mock-data UI.
4. Do not configure production deployment, public access, or paid AI services unless explicitly requested.
5. At the end of each task, summarize changes, tests, unresolved questions, and the next logical step.
