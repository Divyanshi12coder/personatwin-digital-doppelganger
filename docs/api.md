# API reference

Base path: `/api`. Interactive OpenAPI docs: **`/api/docs`** (schema at `/api/openapi.json`).

- Auth: `Authorization: Bearer <access_token>` on every endpoint except health, signup, login and profile options.
- Errors: `{"detail": "human readable message"}`; validation errors also include `errors: [{field, message}]`.
- Status codes: `200`, `201` created, `204` no content, `400` bad request, `401` unauthenticated/revoked,
  `404` not found **or not yours**, `409` conflict, `422` validation, `429` rate-limited, `502/503` AI or database unavailable.

## Health

| Method | Path | Response |
| --- | --- | --- |
| GET | `/health` | `{status, database, database_engine, ai: {mode, provider, model}, embeddings, version}` |

## Auth

| Method | Path | Body | Notes |
| --- | --- | --- | --- |
| POST | `/auth/signup` | `{email, full_name, password}` | `201` → `{access_token, token_type, expires_in, user}`. Password 8–72 bytes with a letter and a digit. `409` if the email exists |
| POST | `/auth/login` | `{email, password}` | `401` with the same message for unknown email or wrong password |
| GET | `/auth/me` | — | `{id, email, full_name, created_at, onboarding_completed}` |
| PATCH | `/auth/me` | `{full_name}` | |
| POST | `/auth/logout` | — | `204`; increments `token_version` → all issued tokens are revoked |
| POST | `/auth/change-password` | `{current_password, new_password}` | Returns a fresh token; other sessions are revoked |
| DELETE | `/auth/me` | `{password}` | `204`; deletes the account and all data |
| GET | `/auth/export` | — | Everything stored about the account (embeddings excluded) |

Auth endpoints are rate limited per IP (`AUTH_RATE_LIMIT_PER_MINUTE`).

## Profile & settings

| Method | Path | Body / response |
| --- | --- | --- |
| GET | `/profile/options` | Allowed persona values with descriptions, experience types, knowledge categories, mentoring domains |
| GET | `/profile` | `{mentor, personality, completeness, missing}` |
| POST | `/profile/onboarding` | `{mentor: MentorProfileIn, personality: PersonalityIn}` → marks onboarding complete |
| PUT | `/profile/mentor` | `{mentor_name, bio, expertise_areas[], mentoring_domains[]}` |
| PUT | `/profile/personality` | `{communication_style, tone, teaching_approach, decision_style, encouragement_style, response_length, formality, directness, warmth, humor (0–100), values[], signature_phrases[], philosophy_encouragement, philosophy_mistakes, philosophy_decisions, philosophy_teaching, boundaries}` |
| GET / PUT | `/settings` | `{save_conversations, use_conversation_memory, auto_remember, retrieval_top_k (1–12), min_relevance (0–0.9), creativity (0–1), show_sources}` |

## Knowledge

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/knowledge?q=&category=&tag=&limit=&offset=` | `{items: KnowledgeOut[], total}`; `q` is a keyword filter on title/content |
| POST | `/knowledge` | `{title, content, category, source_type: text\|note, source?, tags[]}` → `201 KnowledgeOut` |
| POST | `/knowledge/upload` | multipart: `file` (.txt/.md/.pdf, ≤ 2 MB), `title?`, `category`, `tags` (comma-separated) |
| POST | `/knowledge/url` | `{url, title?, category, tags[]}` — public http(s) pages only |
| GET | `/knowledge/{id}` | |
| PATCH | `/knowledge/{id}` | any of `{title, content, category, source, tags}`; content changes re-index |
| DELETE | `/knowledge/{id}` | `204` |

`KnowledgeOut = {id, title, content, category, source_type, source, char_count, chunk_count, indexed, tags[], created_at, updated_at}`

## Experiences

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/experiences?q=&experience_type=&tag=` | `ExperienceOut[]` |
| POST | `/experiences` | `{title, experience_type, situation, what_happened, lesson_learned, do_differently, context, occurred_on?, importance (1–5), tags[]}`; at least one of situation / what happened / lesson required; date not in the future |
| GET / PATCH / DELETE | `/experiences/{id}` | |

## Memories (inspector)

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/memories?q=&type=&limit=` | Without `q`: every memory, newest first, plus persona preferences. With `q`: semantic search with `relevance`. `type` ∈ knowledge, experience, conversation, preference. Response `{items: MemoryItem[], counts, query}` |
| GET | `/memories/tags` | `[{name, count}]` |
| POST | `/memories/reindex` | Re-embed everything; returns counts |
| GET | `/memories/conversation` | Conversation memories |
| GET / PATCH / DELETE | `/memories/conversation/{id}` | PATCH `{title?, content?, tags?}` |

`MemoryItem = {id: "<type>:<id>", ref_id, type, title, category, snippet, tags[], source, date, relevance, indexed}`

## Chat & conversations

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/chat` | `{message (1–4000 chars), conversation_id?, history?[]}`. `history` is only used in privacy mode. Rate limited per user |
| POST | `/chat/messages/{id}/regenerate` | Re-runs the pipeline for the question before this reply; updates it in place |
| PATCH | `/chat/messages/{id}/feedback` | `{feedback: "up" \| "down" \| null}` |
| POST | `/chat/messages/{id}/remember` | `201 {memory_id}` — saves the exchange as a conversation memory |
| GET | `/conversations` | `[{id, title, topic, created_at, updated_at, message_count, last_message}]` |
| GET | `/conversations/{id}` | `{…, messages: MessageOut[]}` |
| PATCH | `/conversations/{id}` | `{title}` |
| DELETE | `/conversations/{id}` | `204` (saved conversation memories are kept) |

```jsonc
// ChatResponse
{
  "conversation_id": 12,            // null in privacy mode
  "conversation_title": "Should I switch careers?",
  "persisted": true,
  "user_message": { "id": 40, "role": "user", "content": "…", "created_at": "…" },
  "assistant_message": {
    "id": 41,
    "role": "assistant",
    "content": "This connects to something I've actually recorded: … [E1]",
    "topic": "career",
    "grounding": "grounded",          // grounded | partial | ungrounded
    "provider": "anthropic",
    "model": "claude-opus-5",
    "latency_ms": 5321,
    "feedback": null,
    "sources": [
      { "label": "E1", "source_type": "experience", "source_id": 3,
        "title": "Leaving agency life…", "snippet": "…", "score": 0.47, "cited": true }
    ],
    "trace": {
      "steps": [ { "step": "understand", "ms": 0, "detail": "Career · decision" }, "…" ],
      "topic": "career", "intent": "decision",
      "unsupported_memory_claim": false, "notice": null, "degraded": false
    }
  },
  "remembered_memory_id": null
}
```

## Insights

| Method | Path | Response |
| --- | --- | --- |
| GET | `/insights/overview` | counts, profile summary + completeness, memory health (indexed ratio, issues), active topics (30 days), recent conversations, AI mode |
| GET | `/insights/analytics?days=7–365` | topics, knowledge categories, experience types, daily conversation trend, sessions per week, cumulative memory growth, top tags, feedback, grounding distribution |
