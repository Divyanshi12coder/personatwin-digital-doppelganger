# Memory system

PersonaTwin separates memory by **what it is** and **how much it can be trusted**.

| Memory | What it holds | Table(s) | Lifetime |
| --- | --- | --- | --- |
| **Short-term** | The current conversation | `messages` (or the browser tab in privacy mode) | One conversation; last 10 turns go into the prompt |
| **Long-term semantic** | Facts, notes, frameworks, documents, web pages | `knowledge_documents`, `knowledge_chunks` | Until the user deletes it |
| **Episodic** | Specific lived experiences, structured as stories | `experience_memories` | Until the user deletes it |
| **Persona** | How the mentor communicates: style, tone, values, philosophy | `personality_profiles`, `mentor_profiles` | Always loaded |
| **Conversation memories** | Exchanges the user chose to keep (or auto-remember) | `conversation_memories` | Until the user deletes it |

Only **episodic** memories may be spoken of as personal memories. Knowledge is "from my notes"; conversation memories are
labelled as partly AI-generated; persona memory shapes the voice and never supplies facts.

## Write path — `services/indexing.py`

```mermaid
flowchart LR
  T[Text / upload / URL] --> X[Extract text<br/>pypdf · HTML parser]
  X --> C[chunk_text<br/>~900 chars, ~150 overlap]
  C --> H[prefix 'title (category)']
  H --> E[embed → 384-d, L2-normalised]
  E --> S[(knowledge_chunks.embedding)]
  EX[Experience fields + tags] --> E2[embed] --> S2[(experience_memories.embedding)]
```

- **Chunking** (`services/chunking.py`): paragraphs are packed greedily up to the chunk size; oversize paragraphs split on
  sentences, then on characters; each new chunk starts with a word-aligned overlap from the previous one.
- **Editing** a document's title, content or category re-chunks and re-embeds it; tag-only edits don't.
- **Failures** never lose data: if the embedding provider is unreachable, the row is saved with `embedding = NULL`, shows as
  *Not indexed*, and Memory health suggests a re-index (`POST /api/memories/reindex`).

## Embeddings — `services/embeddings.py`

| Provider | Setting | Notes |
| --- | --- | --- |
| Local hashing (default) | `EMBEDDING_PROVIDER=local` | Stemmed unigrams, bigrams, character 4-grams and a small concept lexicon (career, change, learning, decision, fear, failure, …) hashed into 384 signed buckets. Deterministic, offline, free. Lexical rather than deeply semantic. |
| OpenAI | `EMBEDDING_PROVIDER=openai` | `text-embedding-3-small` with `dimensions=384` so it fits the same column. |

Vectors from different providers aren't comparable — re-index after switching.

## Read path — `services/retrieval.py`

1. Embed the query; extract query stems.
2. For each store, rank by cosine similarity **for this user only**:
   - PostgreSQL: `SELECT …, embedding <=> :q AS distance … WHERE user_id = :me ORDER BY distance LIMIT n` (HNSW index).
   - SQLite: the same ranking computed in Python.
3. Re-score (hybrid): `score = cosine + 0.12 × (share of query stems found in the text)`.
   - experiences: `+ 0.015 × (importance − 3)`
   - conversation memories: `× 0.9` (they're partly AI-generated)
4. Keep the best chunk per document; limit per type (knowledge `top_k`, experiences `⌈top_k/2⌉` (min 2), notes 2).
5. Drop anything below the user's **minimum relevance** (default 0.12).
6. Chat only: drop anything below **55 % of the best score** (relative cutoff), so a strong match isn't diluted by weak ones.

The Memory Inspector's search box runs the same retrieval (without cutoffs) and shows the scores — a direct way to see what
the mentor would recall.

## User controls

| Setting | Effect |
| --- | --- |
| Save conversation history | Off = privacy mode: nothing about chats is stored; the client sends recent turns for short-term memory |
| Use saved conversation memories | Include/exclude `C#` items from retrieval |
| Automatically remember exchanges | Every answered question becomes a conversation memory |
| Memories retrieved per question | top-k (1–12) |
| Minimum relevance | 0–0.6 |
| Show sources | Hide/show the sources panel and clickable citations |

Everything is inspectable and deletable from the Memory Inspector, and exportable as JSON from Settings.
