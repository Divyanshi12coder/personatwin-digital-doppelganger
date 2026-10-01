import { api } from "./api";
import type {
  Analytics,
  ChatMessage,
  ChatResponse,
  Conversation,
  ConversationDetail,
  ConversationMemory,
  Experience,
  ExperienceInput,
  Health,
  KnowledgeInput,
  KnowledgeItem,
  KnowledgeList,
  MemoryList,
  MemoryType,
  MentorProfileInput,
  Options,
  Overview,
  Personality,
  Profile,
  TagCount,
  TokenResponse,
  User,
  UserSettings,
} from "@/types/api";

const qs = (params: Record<string, string | number | undefined | null>) => {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") search.set(k, String(v));
  });
  const s = search.toString();
  return s ? `?${s}` : "";
};

export const authApi = {
  signup: (body: { email: string; full_name: string; password: string }) =>
    api.post<TokenResponse>("/auth/signup", body),
  login: (body: { email: string; password: string }) => api.post<TokenResponse>("/auth/login", body),
  me: () => api.get<User>("/auth/me"),
  updateMe: (full_name: string) => api.patch<User>("/auth/me", { full_name }),
  logout: () => api.post<void>("/auth/logout"),
  changePassword: (current_password: string, new_password: string) =>
    api.post<TokenResponse>("/auth/change-password", { current_password, new_password }),
  deleteAccount: (password: string) => api.del<void>("/auth/me", { password }),
  exportData: () => api.get<Record<string, unknown>>("/auth/export"),
};

export const healthApi = {
  get: () => api.get<Health>("/health"),
};

export const profileApi = {
  get: () => api.get<Profile>("/profile"),
  options: () => api.get<Options>("/profile/options"),
  onboarding: (mentor: MentorProfileInput, personality: Personality) =>
    api.post<Profile>("/profile/onboarding", { mentor, personality }),
  updateMentor: (mentor: MentorProfileInput) => api.put<Profile>("/profile/mentor", { ...mentor }),
  updatePersonality: (personality: Personality) => api.put<Profile>("/profile/personality", { ...personality }),
  settings: () => api.get<UserSettings>("/settings"),
  updateSettings: (s: UserSettings) => api.put<UserSettings>("/settings", { ...s }),
};

export const knowledgeApi = {
  list: (params: { q?: string; category?: string; tag?: string } = {}) =>
    api.get<KnowledgeList>(`/knowledge${qs({ ...params, limit: 100 })}`),
  get: (id: number) => api.get<KnowledgeItem>(`/knowledge/${id}`),
  create: (body: KnowledgeInput) => api.post<KnowledgeItem>("/knowledge", { ...body }),
  update: (id: number, body: Partial<KnowledgeInput>) => api.patch<KnowledgeItem>(`/knowledge/${id}`, { ...body }),
  remove: (id: number) => api.del<void>(`/knowledge/${id}`),
  upload: (file: File, meta: { title?: string; category: string; tags: string[] }) => {
    const form = new FormData();
    form.append("file", file);
    if (meta.title) form.append("title", meta.title);
    form.append("category", meta.category);
    form.append("tags", meta.tags.join(","));
    return api.post<KnowledgeItem>("/knowledge/upload", form);
  },
  importUrl: (body: { url: string; title?: string; category: string; tags: string[] }) =>
    api.post<KnowledgeItem>("/knowledge/url", { ...body }),
};

export const experienceApi = {
  list: (params: { q?: string; experience_type?: string; tag?: string } = {}) =>
    api.get<Experience[]>(`/experiences${qs(params)}`),
  get: (id: number) => api.get<Experience>(`/experiences/${id}`),
  create: (body: ExperienceInput) => api.post<Experience>("/experiences", { ...body }),
  update: (id: number, body: Partial<ExperienceInput>) => api.patch<Experience>(`/experiences/${id}`, { ...body }),
  remove: (id: number) => api.del<void>(`/experiences/${id}`),
};

export const memoryApi = {
  list: (params: { q?: string; type?: MemoryType | "" } = {}) => api.get<MemoryList>(`/memories${qs(params)}`),
  tags: () => api.get<TagCount[]>("/memories/tags"),
  reindex: () => api.post<Record<string, number>>("/memories/reindex"),
  getConversation: (id: number) => api.get<ConversationMemory>(`/memories/conversation/${id}`),
  updateConversation: (id: number, body: { title?: string; content?: string; tags?: string[] }) =>
    api.patch<ConversationMemory>(`/memories/conversation/${id}`, body),
  removeConversation: (id: number) => api.del<void>(`/memories/conversation/${id}`),
};

export const chatApi = {
  send: (body: { message: string; conversation_id?: number | null; history?: { role: string; content: string }[] }) =>
    api.post<ChatResponse>("/chat", body),
  regenerate: (messageId: number) => api.post<ChatMessage>(`/chat/messages/${messageId}/regenerate`),
  feedback: (messageId: number, feedback: "up" | "down" | null) =>
    api.patch<ChatMessage>(`/chat/messages/${messageId}/feedback`, { feedback }),
  remember: (messageId: number) => api.post<{ memory_id: number }>(`/chat/messages/${messageId}/remember`),
  conversations: () => api.get<Conversation[]>("/conversations"),
  conversation: (id: number) => api.get<ConversationDetail>(`/conversations/${id}`),
  rename: (id: number, title: string) => api.patch<Conversation>(`/conversations/${id}`, { title }),
  removeConversation: (id: number) => api.del<void>(`/conversations/${id}`),
};

export const insightsApi = {
  overview: () => api.get<Overview>("/insights/overview"),
  analytics: (days = 90) => api.get<Analytics>(`/insights/analytics?days=${days}`),
};
