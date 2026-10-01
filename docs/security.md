# Security

## Authentication

- **Password hashing**: bcrypt with 12 rounds (`app/core/security.py`). Passwords are 8–72 bytes (bcrypt's limit) and must
  contain a letter and a digit.
- **Login**: identical `401` message for unknown email and wrong password; a dummy bcrypt check runs for unknown emails so
  response time doesn't reveal which accounts exist.
- **JWT**: HS256 signed with `JWT_SECRET`, `exp`/`iat`/`sub`/`type` claims plus `ver` = the user's `token_version`.
  - `POST /auth/logout` increments `token_version` → every token issued before is rejected (sign-out everywhere).
  - Password change does the same and returns a fresh token for the current session.
- **Production guard**: with `ENVIRONMENT=production` the app refuses to start unless `JWT_SECRET` is ≥ 32 characters and not
  the development default.
- **Token storage**: the SPA keeps the bearer token in `localStorage` (cross-site cookie setup between Vercel and Render was
  deliberately avoided). Mitigations: no `dangerouslySetInnerHTML` anywhere — model output is rendered by a React-element
  mini-markdown renderer — plus short-ish expiry and server-side revocation. An httpOnly-cookie option is on the roadmap.

## Authorization & data isolation

- `get_current_user` (dependency) validates the token, loads the user, checks `is_active` and `token_version`.
- Every private query includes `WHERE user_id = :current_user` — including vector search, tag lookups, aggregations, and
  the "previous question" lookup used by regenerate.
- Objects owned by someone else return **404**, never 403, so IDs can't be probed.
- `knowledge_chunks.user_id` is denormalised so vector search filters by owner without trusting a join.
- Tags are unique per user, not global.
- `tests/test_isolation.py` verifies 15 cross-user endpoints (read/update/delete knowledge, experiences, conversations,
  messages, conversation memories), continuing someone else's conversation, every listing, semantic search, tags, insights,
  and that chat retrieval never surfaces another user's memories.

## Input validation

- Pydantic schemas enforce types, lengths, enums (persona options, categories, experience types), ranges (sliders 0–100,
  importance 1–5, top-k 1–12) and dates (no future experience dates).
- Validation errors return `422` with a readable `detail` and a per-field `errors` list.

## Uploads and URL import (`services/importers.py`)

- Uploads: extensions `.txt .md .markdown .pdf`, max 2 MB (`MAX_UPLOAD_BYTES`), PDFs must start with `%PDF`, text capped at
  200 000 characters, filenames are reduced to their base name.
- URL import (SSRF protection): only `http`/`https`; no embedded credentials; the host is resolved and **every address
  must be globally routable** (`ip.is_global`) — private, loopback, link-local, CGNAT `100.64.0.0/10`, multicast,
  reserved and unspecified addresses are refused; redirects are followed manually (max 3) and each
  hop is re-checked; only HTML/plain-text content types; download capped at 2 MB; 10 s timeout.
  *Known limitation:* a DNS-rebinding attacker could change the record between the check and the request; for hostile
  environments run the backend behind an egress proxy that enforces the same rules.

## Prompt injection

Imported pages and documents are user-controlled text. They are placed inside `<memory_context>` and the system prompt says
that text there is reference data whose instructions must not be followed. Our own framing tags (`<memory_context>`,
`<analysis>`) are stripped from memory content, titles and the user's question first, so imported text cannot close the
block early and place instructions outside it. Validation also strips any echoed internal tags
and invented citations. This reduces — but, as with any LLM system, cannot fully eliminate — injection risk; the blast
radius is limited to the user's own mentor because nothing is shared across accounts.

## Secrets

- AI and embedding keys exist only in backend environment variables. The browser calls only `/api/*` on the PersonaTwin
  backend; there is no provider SDK or key in the frontend bundle.
- `.env` files are git-ignored; `.env.example` contains no secrets. `render.yaml` marks `AI_API_KEY` as `sync: false` and
  generates `JWT_SECRET`.

## HTTP hardening

- CORS allow-list from `CORS_ORIGINS`; no credentials mode (bearer tokens only).
- `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` from the API,
  nginx and Vercel.
- In-process sliding-window rate limits: auth endpoints per client IP, chat per user (use Redis for multi-instance
  deployments). The client IP is `request.client.host`; a client-supplied `X-Forwarded-For` is never trusted directly.
  Behind a proxy, uvicorn's `--proxy-headers` rewrites the client address only for proxies listed in
  `FORWARDED_ALLOW_IPS` (default `127.0.0.1`; the Compose file trusts the private Docker network, Render uses `*`
  because the service is only reachable through Render's proxy).
- Database errors are logged server-side and returned as a generic `503`.
- The backend container runs as a non-root user.

## Privacy controls for users

Privacy mode (no conversation storage), opt-in conversation memory, per-item delete, full JSON export, and account deletion
that cascades to every row the user owns.
