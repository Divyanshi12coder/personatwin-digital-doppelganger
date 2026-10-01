<p align="center">
  <img src="docs/images/banner.svg" alt="PersonaTwin — Meet the version of you that never forgets what you've learned." width="100%" />
</p>

<h1 align="center">PersonaTwin — Digital Doppelganger Mentor</h1>

<p align="center">
  AI-powered digital mentor that combines personality modeling, long-term memory, RAG, and conversational AI to provide personalized guidance.
</p>

<p align="center">
  <img alt="React" src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white&labelColor=4A2C1A" />
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white&labelColor=4A2C1A" />
  <img alt="Vite" src="https://img.shields.io/badge/Vite-7-646CFF?logo=vite&logoColor=white&labelColor=4A2C1A" />
  <img alt="Tailwind CSS" src="https://img.shields.io/badge/Tailwind_CSS-3-06B6D4?logo=tailwindcss&logoColor=white&labelColor=4A2C1A" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white&labelColor=4A2C1A" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white&labelColor=4A2C1A" />
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white&labelColor=4A2C1A" />
  <img alt="pgvector" src="https://img.shields.io/badge/pgvector-HNSW-D4A017?labelColor=4A2C1A" />
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white&labelColor=4A2C1A" />
  <img alt="JWT" src="https://img.shields.io/badge/Auth-JWT-000000?logo=jsonwebtokens&logoColor=white&labelColor=4A2C1A" />
  <img alt="Claude" src="https://img.shields.io/badge/LLM-Claude_%7C_OpenAI_%7C_Demo-D4A017?labelColor=4A2C1A" />
  <img alt="License" src="https://img.shields.io/badge/License-MIT-E7B84B?labelColor=4A2C1A" />
  <img alt="Status" src="https://img.shields.io/badge/Status-Active_development-806B5A?labelColor=4A2C1A" />
</p>

<p align="center">
  <b>Live demo:</b> <i>coming soon — deploy your own in minutes with <a href="docs/deployment.md">Vercel + Render</a></i>
</p>

---

## What is PersonaTwin?

PersonaTwin is **not a chatbot with a personality prompt**. It is a full-stack memory system that turns a person's
**knowledge**, **lived experiences** and **mentoring style** into a personal AI mentor:

```
User knowledge + experiences + personality profile + communication style
      + long-term memory + semantic retrieval + LLM reasoning
      = a personalized digital mentor that answers from *your* memories
```

The system keeps four kinds of information strictly apart — **facts** (knowledge), **episodes** (experiences),
**preferences** (persona) and **AI-generated text** (conversations) — so the mentor can never pass off a generated
answer as a real memory. Every reply cites the memories it used, and when nothing relevant is stored the mentor says
so plainly instead of inventing a story.

<p align="center">
  <img src="docs/images/hero.png" alt="PersonaTwin landing page hero" width="100%" />
</p>

## Screenshots

| Mentor chat (grounded, cited answer) | Dashboard |
| --- | --- |
| <img src="docs/images/mentor-chat.png" alt="Mentor chat with cited memories" /> | <img src="docs/images/dashboard.png" alt="Dashboard with memory health and profile completeness" /> |
| **Memory Inspector (semantic recall test)** | **Knowledge Vault** |
| <img src="docs/images/memory-vault.png" alt="Memory inspector with relevance scores" /> | <img src="docs/images/knowledge-vault.png" alt="Knowledge vault" /> |
| **Experiences (episodic memory)** | **Personality profile** |
| <img src="docs/images/experiences.png" alt="Experiences journal" /> | <img src="docs/images/personality.png" alt="Personality profile with radar chart" /> |
| **Insights (live analytics)** | **Mobile** |
| <img src="docs/images/insights.png" alt="Insights charts" /> | <img src="docs/images/mobile-chat.png" alt="Mobile chat" width="260" /> |

> Screenshots are captured from the running app with demo-mode replies (no LLM key configured).

## Features

| Area | What it does |
| --- | --- |
| **Landing page** | Editorial "mentor's study" design with original SVG illustrations (notebook, fountain pen, chalkboard, classroom, knowledge graph) |
| **Auth** | Sign up / log in / log out with bcrypt + JWT; server-side token revocation; protected routes |
| **Onboarding** | 4-step wizard: basics → voice & style → mentoring philosophy → review |
| **Dashboard** | Memory counts, profile completeness, memory-health checks, composition chart, active topics, recent conversations |
| **Knowledge Vault** | Write notes, upload `.txt/.md/.pdf`, or import a public URL; chunked + embedded; search, filter by category/tag, edit, delete |
| **Experiences** | Structured episodes — situation, what happened, what I learned, what I'd do differently, context, date, importance, tags |
| **Personality** | Option cards + sliders + values + philosophy, radar preview; explicitly a communication profile, not a diagnosis |
| **Mentor Chat** | Conversation history, typing indicator, timestamps, clickable citations, sources panel with relevance, pipeline trace, regenerate, copy, 👍/👎 feedback, "Remember this" |
| **Memory Inspector** | One view of knowledge, experiences, preferences and conversation memories; semantic recall test with relevance scores; edit & delete |
| **Insights** | Topics, sessions per week, conversation trend, memory growth, categories, tags, feedback & grounding — all from your real data |
| **Settings** | Profile, AI behaviour (creativity, top-k, min relevance, sources), memory controls (privacy mode, auto-remember), re-index, JSON export, password change, account deletion |

## Architecture

<p align="center"><img src="docs/images/architecture.svg" alt="System architecture" width="100%" /></p>

```mermaid
flowchart LR
  subgraph Browser["Browser — React + TypeScript (Vite)"]
    UI[Pages & components] --> Client[Typed API client<br/>JWT bearer]
  end
  subgraph API["FastAPI backend"]
    Routers[Routers + DI<br/>auth · profile · knowledge · experiences<br/>memories · chat · insights] --> Orchestrator[Chat orchestrator]
    Routers --> Indexing[Write path<br/>chunk → embed → store]
    Orchestrator --> AIS[AIService<br/>Anthropic · OpenAI · Demo]
    Orchestrator --> Ret[Retrieval<br/>pgvector cosine + lexical bonus]
    Indexing --> Emb[Embedder<br/>local hashing · OpenAI]
  end
  subgraph DB["PostgreSQL 16 + pgvector"]
    Tables[(users · profiles · knowledge · chunks<br/>experiences · conversations · messages<br/>message_sources · conversation_memories · tags)]
  end
  Client -- "HTTPS /api" --> Routers
  Ret -- "SQL WHERE user_id = :me" --> Tables
  Indexing --> Tables
  AIS -. "server-side only" .-> LLM[(Claude / OpenAI)]
```

More detail: [docs/architecture.md](docs/architecture.md)

## AI architecture

```mermaid
flowchart TD
  Q[User query] --> U[1 · Query understanding<br/>topic · intent · personal-experience check]
  U --> R{2 · Memory retrieval<br/>scoped to the user}
  R --> K[Knowledge chunks<br/>long-term semantic]
  R --> E[Experiences<br/>episodic]
  R --> C[Saved conversation notes<br/>opt-in, AI-assisted]
  P[3 · Persona memory<br/>style · tone · values · philosophy] --> A
  K & E & C --> A[4 · Context assembly<br/>labels K# E# C# · budget]
  H[Short-term memory<br/>last 10 turns] --> PR
  A --> PR[5 · Prompt construction<br/>grounding rules]
  PR --> L[6 · LLM<br/>Claude · OpenAI · Demo composer]
  L --> V[7 · Response validation<br/>invalid citations removed<br/>unsupported 'memories' flagged]
  V --> OUT[Reply + sources + trace]
  V --> S[8 · Optional storage<br/>messages · source snapshots · conversation memory]
```

- **The LLM is never the source of truth for memories.** Everything personal comes from rows retrieved for this user.
- **Grounding rules** in the system prompt require `[K1]`/`[E2]`-style citations and forbid inventing personal stories.
- **Validation** strips citations to memories that were not retrieved, and appends a transparency note when the reply says
  "I remember…" without citing an experience.
- **Provider abstraction**: `AI_PROVIDER=anthropic` uses the official `anthropic` SDK (default `claude-opus-5`, adaptive
  thinking, server-side refusal fallbacks); `openai` uses Chat Completions (or any compatible gateway); `demo` needs no key.
  If a live provider fails at request time, the reply is composed by the demo composer and labelled with a notice.

More detail: [docs/ai-system.md](docs/ai-system.md)

## Memory architecture

| Memory | Stored in | Retrieved by | May be spoken of as "I remember…"? |
| --- | --- | --- | --- |
| **Short-term** — current conversation | `messages` (or the browser tab in privacy mode) | last 10 turns | — |
| **Long-term semantic** — knowledge | `knowledge_documents` → `knowledge_chunks.embedding` | vector similarity | No — "from my notes on…" |
| **Episodic** — experiences | `experience_memories.embedding` | vector similarity (+ importance) | **Yes, and only these** |
| **Persona** — preferences | `personality_profiles`, `mentor_profiles` | always loaded | — (shapes voice only) |
| **Conversation memories** | `conversation_memories.embedding` | vector similarity (×0.9) | No — labelled AI-assisted |

More detail: [docs/memory-system.md](docs/memory-system.md)

## RAG pipeline

<p align="center"><img src="docs/images/rag-pipeline.svg" alt="RAG pipeline" width="100%" /></p>

1. **Chunking** — paragraph-aware packing to ~900 characters with ~150 characters of overlap; long paragraphs split on sentences.
2. **Embeddings** — 384-dimensional, L2-normalised. `local` (default): deterministic hashed unigrams/bigrams/character
   n-grams plus a small concept lexicon — offline, free, lexical. `openai`: `text-embedding-3-small` reduced to 384 dims.
3. **Vector storage** — `vector(384)` columns with **HNSW** cosine indexes created by the Alembic migration.
4. **Similarity search** — `embedding <=> :query` in SQL, always `WHERE user_id = :current_user`, best chunk per document.
5. **Metadata filtering** — category filter, per-type limits, importance boost for experiences.
6. **Top-k + thresholds** — user-tunable top-k and minimum relevance, plus a relative cutoff (55 % of the best match) so loosely related memories stay out of the prompt.
7. **Context assembly** — labelled, score-ordered, 9 000-character budget.

## Database

<p align="center"><img src="docs/images/database.svg" alt="Database schema" width="100%" /></p>

```mermaid
erDiagram
  users ||--o| mentor_profiles : has
  users ||--o| personality_profiles : has
  users ||--o| user_settings : has
  users ||--o{ knowledge_documents : owns
  knowledge_documents ||--o{ knowledge_chunks : "split into"
  users ||--o{ experience_memories : owns
  users ||--o{ conversations : owns
  conversations ||--o{ messages : contains
  messages ||--o{ message_sources : "grounded by"
  users ||--o{ conversation_memories : owns
  users ||--o{ tags : owns
  tags }o--o{ knowledge_documents : labels
  tags }o--o{ experience_memories : labels
  tags }o--o{ conversation_memories : labels
```

Normalised tables with foreign keys and timestamps; small string lists (expertise, values) are JSON arrays, every scalar trait has its own column. Migrations live in [`backend/alembic`](backend/alembic).

## API

REST under `/api`, Pydantic-validated, OpenAPI docs at **`/api/docs`**.

| Group | Endpoints |
| --- | --- |
| Health | `GET /api/health` |
| Auth | `POST /auth/signup` · `POST /auth/login` · `GET/PATCH/DELETE /auth/me` · `POST /auth/logout` · `POST /auth/change-password` · `GET /auth/export` |
| Profile | `GET /profile` · `GET /profile/options` · `POST /profile/onboarding` · `PUT /profile/mentor` · `PUT /profile/personality` · `GET/PUT /settings` |
| Knowledge | `GET/POST /knowledge` · `POST /knowledge/upload` · `POST /knowledge/url` · `GET/PATCH/DELETE /knowledge/{id}` |
| Experiences | `GET/POST /experiences` · `GET/PATCH/DELETE /experiences/{id}` |
| Memories | `GET /memories?q=&type=` · `GET /memories/tags` · `POST /memories/reindex` · `GET/PATCH/DELETE /memories/conversation/{id}` |
| Chat | `POST /chat` · `POST /chat/messages/{id}/regenerate` · `PATCH /chat/messages/{id}/feedback` · `POST /chat/messages/{id}/remember` |
| Conversations | `GET /conversations` · `GET/PATCH/DELETE /conversations/{id}` |
| Insights | `GET /insights/overview` · `GET /insights/analytics?days=` |

Full reference with request/response shapes: [docs/api.md](docs/api.md)

## Security

- **Passwords**: bcrypt (12 rounds), 8–72 bytes with a letter and a number; constant-time-ish login for unknown emails.
- **JWT**: HS256, expiry, and a `token_version` claim — logout and password changes revoke every issued token.
- **Isolation**: every private query filters by the authenticated `user_id`; foreign IDs return `404`, never `403`, so
  existence isn't leaked. A dedicated test suite ([`tests/test_isolation.py`](backend/tests/test_isolation.py)) checks
  15 cross-user endpoints, listings, semantic search, tags and chat retrieval.
- **Input validation**: Pydantic schemas with lengths, enums and ranges; friendly `422` messages.
- **Rate limits** use the real client address — forged `X-Forwarded-For` headers are ignored unless they come from a
  proxy listed in `FORWARDED_ALLOW_IPS`.
- **Uploads**: `.txt/.md/.pdf` only, 2 MB cap, PDF magic-byte check. **URL import**: http(s) only, only globally routable
  addresses (private, loopback, link-local, CGNAT refused — SSRF), every redirect re-checked, size-capped.
- **Prompt injection**: imported content is wrapped as *data* in `<memory_context>` (with our framing tags stripped from it)
  and the model is told not to follow instructions inside it.
- **Keys**: AI keys live only in backend env vars; the browser never calls a provider. `.env` files are git-ignored.
- **Production guard**: `ENVIRONMENT=production` refuses to boot with a weak `JWT_SECRET`.
- Rate limits on auth and chat; CORS allow-list; `nosniff` / `DENY` framing headers.

More detail: [docs/security.md](docs/security.md)

## Tech stack

**Frontend** React 18 · TypeScript · Vite 7 · Tailwind CSS 3 · Framer Motion · Lucide React · Recharts · React Router 7
**Backend** Python 3.12+ · FastAPI · Pydantic 2 · SQLAlchemy 2 · Alembic · PyJWT · bcrypt · httpx · pypdf
**Data** PostgreSQL 16 · pgvector (HNSW, cosine)
**AI** Anthropic Claude (official SDK) · OpenAI-compatible Chat Completions · OpenAI or local embeddings
**Infra** Docker · Docker Compose · nginx · Vercel · Render
**Testing** pytest (API + service tests) · `tsc --noEmit` · Vite production build

## Project structure

```
personatwin-digital-doppelganger/
├── backend/
│   ├── app/
│   │   ├── api/            # deps.py (auth/DB injection) + routes/*
│   │   ├── core/           # config, security (bcrypt/JWT), rate limiting
│   │   ├── db/             # Base, session, EmbeddingVector type
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── services/       # chat pipeline, retrieval, embeddings, AI providers, …
│   │   └── main.py
│   ├── alembic/            # migrations (pgvector extension + HNSW indexes)
│   ├── tests/              # pytest suite
│   ├── Dockerfile
│   └── requirements*.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # ui/, chat/, memory/, persona/, illustrations/, layout/
│   │   ├── config/         # visuals registry (all imagery in one place)
│   │   ├── context/        # Auth, Toast, Options providers
│   │   ├── hooks/ layouts/ pages/ services/ types/ utils/
│   ├── nginx.conf · vercel.json · Dockerfile
├── docs/                   # architecture, ai-system, memory-system, api, security, deployment + images/
├── docker-compose.yml · render.yaml · .env.example
└── README.md
```

## Local setup

**Prerequisites:** Python 3.12+, Node 20.19+ (22 recommended). PostgreSQL is optional for local development.

```bash
# 1. Backend
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp ../.env.example .env              # then edit; for a quick start set DATABASE_URL=sqlite:///./personatwin.db
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev                          # http://localhost:5173 — /api is proxied to :8000
```

Open http://localhost:5173, create an account, and complete onboarding. With no AI key the mentor runs in **demo mode**:
replies are composed directly from the memories retrieval returns (clearly labelled in the UI).

**Enable a real LLM** — set in `backend/.env` and restart:

```bash
AI_PROVIDER=anthropic
AI_API_KEY=sk-ant-...
AI_MODEL=claude-opus-5        # optional; this is the default
```

or `AI_PROVIDER=openai`, `AI_API_KEY=sk-...`, `AI_MODEL=gpt-4o-mini` (`AI_BASE_URL` for compatible gateways).
For stronger semantic retrieval set `EMBEDDING_PROVIDER=openai` and run **Settings → Re-index memories**.

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./personatwin.db` | SQLAlchemy URL. `postgres://` / `postgresql://` are normalised to psycopg 3 |
| `JWT_SECRET` | dev value | **Required ≥ 32 chars in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `720` | Token lifetime |
| `CORS_ORIGINS` | localhost ports | Comma-separated allowed origins |
| `AI_PROVIDER` | `demo` | `anthropic` · `openai` · `demo` |
| `AI_API_KEY` / `AI_MODEL` / `AI_BASE_URL` | — | Provider credentials and model (`claude-opus-5` default for Anthropic) |
| `AI_EFFORT` | `medium` | Anthropic adaptive-thinking effort |
| `AI_ENABLE_FALLBACKS` | `true` | Anthropic server-side refusal fallbacks |
| `EMBEDDING_PROVIDER` | `local` | `local` · `openai` (384-dim) |
| `EMBEDDING_API_KEY` / `EMBEDDING_MODEL` | — / `text-embedding-3-small` | OpenAI embeddings |
| `AUTH_RATE_LIMIT_PER_MINUTE` / `CHAT_RATE_LIMIT_PER_MINUTE` | `20` / `30` | In-process rate limits |
| `FORWARDED_ALLOW_IPS` | `127.0.0.1` | Proxies whose `X-Forwarded-For` uvicorn trusts (container entrypoint) |
| `VITE_API_URL` (frontend) | empty | Backend origin for Vercel builds; empty = same-origin `/api` |

See [`.env.example`](.env.example) for the full list.

## Docker

```bash
cp .env.example .env        # optionally add AI_PROVIDER / AI_API_KEY
docker compose up --build
```

| Service | URL | Notes |
| --- | --- | --- |
| frontend | http://localhost:8080 | nginx serves the SPA and proxies `/api` |
| backend | http://localhost:8000/api/docs | runs `alembic upgrade head` on start |
| postgres | internal | `pgvector/pgvector:pg16`, persistent `pgdata` volume |

Health checks enforce start order: postgres healthy → backend migrated & healthy → frontend.

<p align="center"><img src="docs/images/deployment.svg" alt="Deployment" width="100%" /></p>

Cloud deployment (Vercel + Render): [docs/deployment.md](docs/deployment.md)

## Testing

```bash
cd backend
pytest                                   # 68 tests on in-memory SQLite

# Optional: run the same suite against PostgreSQL + pgvector
TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/personatwin_test pytest

cd ../frontend
npm run typecheck                        # tsc --noEmit
npm run build                            # type-check + production build
```

What the tests cover: signup/login/logout/token revocation/password change/account deletion, validation errors, rate
limiting, knowledge/experience/conversation-memory CRUD, file upload rules, SSRF blocking, **cross-user isolation**, the full
chat pipeline (grounding, "no notes" honesty, personal-question honesty, short-term memory, regenerate, feedback, remember,
privacy mode, auto-remember), provider and embedding-outage degradation, embeddings, chunking, query understanding,
context labelling, response validation, prompt-tag neutralisation, SSRF address rules and forged-header rate limiting.
CI (`.github/workflows/ci.yml`) runs the suite on SQLite and on a `pgvector/pgvector:pg16` service, plus migrations
(upgrade → downgrade → upgrade → drift check) and the frontend build.

## Engineering challenges

- **Keeping generated text from becoming "memory".** Solved structurally: separate stores, labelled context, prompt rules,
  and a validator that removes invented citations and flags unsupported first-person memory claims.
- **One codebase, two databases.** A custom `EmbeddingVector` SQLAlchemy type maps to `vector(384)` on PostgreSQL and to JSON
  on SQLite, so tests run anywhere while production uses pgvector + HNSW.
- **A useful product without an API key.** The demo composer builds answers only from retrieved memories and persona-shaped
  playbooks — honest about being a demo, and still exercising the full pipeline.
- **Lexical embeddings are noisy.** Hybrid scoring (cosine + lexical overlap) and a relative cutoff keep weak matches out of
  the prompt; OpenAI embeddings are one env var away.
- **Privacy mode.** With saving off, nothing is written server-side; the client carries short-term memory instead.

## Key technical decisions

- **pgvector over a separate vector DB** — one transactional store; ownership filters and deletes stay consistent.
- **384-dim embeddings** — fixed by the migration; OpenAI's `dimensions` parameter lets both providers fit it.
- **Deterministic query understanding** — topic/intent detection without an extra LLM round-trip.
- **Bearer tokens + `token_version`** — stateless JWTs that can still be revoked server-side.
- **Original SVG illustrations** instead of stock photos — local, license-free, on-brand, crisp, and centrally registered in `src/config/visuals.ts`.
- **Non-streaming chat** — simpler, and the UI shows the real per-step trace after each answer.

## Roadmap

- [ ] Streaming responses (SSE) with live pipeline steps
- [ ] Local sentence-transformer embeddings option
- [ ] Shareable read-only mentor links for mentees
- [ ] Redis-backed rate limiting for multi-instance deployments
- [ ] httpOnly-cookie session option
- [ ] Spaced "memory review" prompts to keep experiences fresh
- [ ] Playwright end-to-end tests in CI

## Author

Built by **[@Divyanshi12coder](https://github.com/Divyanshi12coder)**.
Issues and pull requests are welcome.

## License

[MIT](LICENSE)

> PersonaTwin offers mentoring perspectives based on the user's own notes. It is not a substitute for professional
> medical, legal, financial or mental-health advice.
