// Types mirroring the backend Pydantic schemas (backend/app/schemas).

export interface User {
  id: number;
  email: string;
  full_name: string;
  created_at: string;
  onboarding_completed: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface MentorProfile {
  mentor_name: string;
  bio: string;
  expertise_areas: string[];
  mentoring_domains: string[];
  onboarding_completed: boolean;
  updated_at: string;
}

export interface MentorProfileInput {
  mentor_name: string;
  bio: string;
  expertise_areas: string[];
  mentoring_domains: string[];
}

export interface Personality {
  communication_style: string;
  tone: string;
  teaching_approach: string;
  decision_style: string;
  encouragement_style: string;
  response_length: string;
  formality: number;
  directness: number;
  warmth: number;
  humor: number;
  values: string[];
  signature_phrases: string[];
  philosophy_encouragement: string;
  philosophy_mistakes: string;
  philosophy_decisions: string;
  philosophy_teaching: string;
  boundaries: string;
}

export interface PersonalityOut extends Personality {
  updated_at: string;
}

export interface Profile {
  mentor: MentorProfile | null;
  personality: PersonalityOut;
  completeness: number;
  missing: string[];
}

export interface OptionItem {
  value: string;
  description: string;
}

export type PersonaOptionKey =
  | "communication_style"
  | "tone"
  | "teaching_approach"
  | "decision_style"
  | "encouragement_style"
  | "response_length";

export interface Options {
  persona: Record<PersonaOptionKey, OptionItem[]>;
  experience_types: OptionItem[];
  knowledge_categories: OptionItem[];
  mentoring_domains: string[];
}

export interface UserSettings {
  save_conversations: boolean;
  use_conversation_memory: boolean;
  auto_remember: boolean;
  retrieval_top_k: number;
  min_relevance: number;
  creativity: number;
  show_sources: boolean;
}

export interface KnowledgeItem {
  id: number;
  title: string;
  content: string;
  category: string;
  source_type: "text" | "note" | "document" | "url";
  source: string;
  char_count: number;
  chunk_count: number;
  indexed: boolean;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface KnowledgeList {
  items: KnowledgeItem[];
  total: number;
}

export interface KnowledgeInput {
  title: string;
  content: string;
  category: string;
  source_type?: "text" | "note";
  source?: string;
  tags: string[];
}

export interface Experience {
  id: number;
  title: string;
  experience_type: string;
  situation: string;
  what_happened: string;
  lesson_learned: string;
  do_differently: string;
  context: string;
  occurred_on: string | null;
  importance: number;
  indexed: boolean;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export type ExperienceInput = Omit<Experience, "id" | "indexed" | "created_at" | "updated_at">;

export interface ConversationMemory {
  id: number;
  title: string;
  content: string;
  topic: string;
  conversation_id: number | null;
  indexed: boolean;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export type MemoryType = "knowledge" | "experience" | "conversation" | "preference";

export interface MemoryItem {
  id: string;
  ref_id: number | null;
  type: MemoryType;
  title: string;
  category: string;
  snippet: string;
  tags: string[];
  source: string;
  date: string | null;
  relevance: number | null;
  indexed: boolean;
}

export interface MemoryList {
  items: MemoryItem[];
  counts: Record<MemoryType, number>;
  query?: string | null;
}

export interface TagCount {
  name: string;
  count: number;
}

export interface Source {
  label: string;
  source_type: "knowledge" | "experience" | "conversation";
  source_id: number;
  title: string;
  snippet: string;
  score: number;
  cited: boolean;
}

export interface TraceStep {
  step: string;
  ms: number;
  detail: string;
}

export interface MessageTrace {
  steps: TraceStep[];
  topic: string;
  intent: string;
  unsupported_memory_claim?: boolean;
  notice?: string | null;
  degraded?: boolean;
}

export interface ChatMessage {
  id: number | null;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  topic: string;
  feedback: "up" | "down" | null;
  grounding: "grounded" | "partial" | "ungrounded" | null;
  provider: string | null;
  model: string | null;
  latency_ms: number | null;
  sources: Source[];
  trace: MessageTrace | null;
  remembered?: boolean;
}

export interface ChatResponse {
  conversation_id: number | null;
  conversation_title: string | null;
  persisted: boolean;
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  remembered_memory_id: number | null;
}

export interface Conversation {
  id: number;
  title: string;
  topic: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message: string | null;
}

export interface ConversationDetail extends Conversation {
  messages: ChatMessage[];
}

export interface Overview {
  counts: {
    knowledge_documents: number;
    knowledge_chunks: number;
    experiences: number;
    conversation_memories: number;
    total_memories: number;
    conversations: number;
    questions_asked: number;
  };
  profile: {
    mentor_name: string | null;
    bio: string;
    expertise_areas: string[];
    mentoring_domains: string[];
    communication_style: string;
    tone: string;
    values: string[];
    completeness: number;
    missing: string[];
  };
  memory_health: {
    status: "healthy" | "needs_attention" | "empty";
    indexed_ratio: number;
    unindexed_items: number;
    categories_covered: number;
    experiences_with_lessons: number;
    issues: string[];
  };
  active_topics: { topic: string; label: string; count: number }[];
  recent_conversations: { id: number; title: string; topic: string; updated_at: string; message_count: number }[];
  ai: { mode: "demo" | "live"; provider: string; model: string };
}

export interface Analytics {
  window_days: number;
  topics: { topic: string; label: string; count: number }[];
  knowledge_categories: { category: string; count: number }[];
  experience_types: { type: string; count: number }[];
  conversation_trend: { date: string; questions: number; replies: number }[];
  sessions_by_week: { week: string; sessions: number }[];
  memory_growth: { date: string; knowledge: number; experiences: number; conversation: number }[];
  top_tags: { tag: string; count: number }[];
  feedback: { up: number; down: number };
  grounding: { grounded: number; partial: number; ungrounded: number };
}

export interface Health {
  status: "ok" | "degraded";
  database: string;
  database_engine: string;
  ai: { mode: "demo" | "live"; provider: string; model: string };
  embeddings: string;
  version: string;
}
