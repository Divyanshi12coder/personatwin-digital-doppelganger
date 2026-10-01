import { AnimatePresence, motion } from "framer-motion";
import { Check, EyeOff, History, MessageCirclePlus, Pencil, RefreshCw, Trash2, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ChatInput } from "@/components/chat/ChatInput";
import { ChatMessage, TypingIndicator } from "@/components/chat/ChatMessage";
import { StickyNote } from "@/components/illustrations/Illustrations";
import { Button } from "@/components/ui/Button";
import { Avatar, Badge, ErrorState, LoadingState, Skeleton } from "@/components/ui/Feedback";
import { ConfirmDialog } from "@/components/ui/Modal";
import { useToast } from "@/context/ToastContext";
import { useAsync, useDocumentTitle } from "@/hooks/useAsync";
import { errorMessage } from "@/services/api";
import { chatApi, insightsApi, profileApi } from "@/services/endpoints";
import type { ChatMessage as Msg, Conversation } from "@/types/api";
import { cn, relativeTime, topicLabel } from "@/utils/format";

const STARTERS = [
  "I'm struggling to decide whether I should switch careers.",
  "How should I approach learning something genuinely hard?",
  "I keep procrastinating on an important project. What would you do?",
  "Have you ever failed at something that mattered? What did you learn?",
];

// Privacy mode: the client carries short-term memory. Keep each turn well under the API's limit.
const toHistory = (msgs: Msg[]) =>
  msgs.slice(-20).map((m) => ({ role: m.role, content: m.content.slice(0, 6000) }));

function ConversationList({
  conversations,
  activeId,
  loading,
  onDelete,
  onNavigate,
}: {
  conversations: Conversation[] | null;
  activeId: number | null;
  loading: boolean;
  onDelete: (c: Conversation) => void;
  onNavigate?: () => void;
}) {
  if (loading && !conversations) {
    return (
      <div className="space-y-2 p-3">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-14" />
        ))}
      </div>
    );
  }
  if (!conversations?.length) {
    return <p className="p-4 text-sm text-muted">No saved conversations yet. Your first question starts one.</p>;
  }
  return (
    <ul className="space-y-1 p-2">
      {conversations.map((c) => (
        <li key={c.id} className="group relative">
          <Link
            to={`/app/chat/${c.id}`}
            onClick={onNavigate}
            aria-current={c.id === activeId ? "page" : undefined}
            className={cn(
              "block rounded-xl px-3 py-2.5 pr-9 transition-colors",
              c.id === activeId ? "bg-softgold/70" : "hover:bg-paper",
            )}
          >
            <p className="truncate text-sm font-medium text-brown">{c.title}</p>
            <p className="truncate text-xs text-muted">
              {topicLabel(c.topic)} · {relativeTime(c.updated_at)}
            </p>
          </Link>
          <button
            type="button"
            onClick={() => onDelete(c)}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-muted opacity-100 hover:bg-red-50 hover:text-red-700 sm:opacity-0 sm:focus:opacity-100 sm:group-hover:opacity-100"
            aria-label={`Delete conversation ${c.title}`}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </li>
      ))}
    </ul>
  );
}

export default function ChatPage() {
  const params = useParams();
  const conversationId = params.conversationId ? Number(params.conversationId) : null;
  const navigate = useNavigate();
  const toast = useToast();

  const settings = useAsync(() => profileApi.settings(), []);
  const overview = useAsync(() => insightsApi.overview(), []);
  const conversations = useAsync(() => chatApi.conversations(), []);

  const [messages, setMessages] = useState<Msg[]>([]);
  const [title, setTitle] = useState<string | null>(null);
  const [loadingConv, setLoadingConv] = useState(false);
  const [convError, setConvError] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<{ message: string; text: string } | null>(null);
  const [regenerating, setRegenerating] = useState(false);
  const [remembered, setRemembered] = useState<Set<number>>(new Set());
  const [historyOpen, setHistoryOpen] = useState(false);
  const [deleting, setDeleting] = useState<Conversation | null>(null);
  const [renaming, setRenaming] = useState<string | null>(null);
  const skipLoadFor = useRef<number | null>(null);
  // The conversation currently on screen; replies that arrive after the user
  // switched away must not be written into the wrong conversation's view.
  const activeConversation = useRef<number | null>(conversationId);
  const [deletingBusy, setDeletingBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const mentorName = overview.data?.profile.mentor_name ?? "Your mentor";
  const privacyMode = settings.data ? !settings.data.save_conversations : false;
  const showSources = settings.data?.show_sources ?? true;
  useDocumentTitle(title ?? "Mentor Chat");

  const loadConversation = useCallback(async (id: number) => {
    setLoadingConv(true);
    setConvError(null);
    try {
      const detail = await chatApi.conversation(id);
      setMessages(detail.messages);
      setTitle(detail.title);
    } catch (err) {
      setConvError(errorMessage(err));
    } finally {
      setLoadingConv(false);
    }
  }, []);

  useEffect(() => {
    activeConversation.current = conversationId;
    setSendError(null);
    if (conversationId === null) {
      setMessages([]);
      setTitle(null);
      return;
    }
    if (skipLoadFor.current === conversationId) {
      skipLoadFor.current = null;
      return;
    }
    void loadConversation(conversationId);
  }, [conversationId, loadConversation]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, sending]);

  const send = async (textArg?: string) => {
    const text = (textArg ?? draft).trim();
    if (!text || sending) return;
    setSendError(null);
    setDraft("");
    const optimistic: Msg = {
      id: null,
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
      topic: "general",
      feedback: null,
      grounding: null,
      provider: null,
      model: null,
      latency_ms: null,
      sources: [],
      trace: null,
    };
    const history = toHistory(messages);
    const startedIn = conversationId;
    setMessages((prev) => [...prev, optimistic]);
    setSending(true);
    try {
      const res = await chatApi.send({
        message: text,
        conversation_id: privacyMode ? null : conversationId,
        history: privacyMode ? history : [],
      });
      if (activeConversation.current !== startedIn) {
        // The user moved to another conversation while we were waiting.
        if (res.persisted) {
          void conversations.reload();
          toast.info(`Your mentor replied in “${res.conversation_title ?? "another conversation"}”.`);
        }
        return;
      }
      setMessages((prev) => [...prev.filter((m) => m !== optimistic), res.user_message, res.assistant_message]);
      if (res.remembered_memory_id && res.assistant_message.id) {
        setRemembered((s) => new Set(s).add(res.assistant_message.id as number));
      }
      if (res.persisted && res.conversation_id && res.conversation_id !== conversationId) {
        skipLoadFor.current = res.conversation_id;
        setTitle(res.conversation_title);
        navigate(`/app/chat/${res.conversation_id}`, { replace: conversationId === null });
      }
      if (res.persisted) void conversations.reload();
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m !== optimistic));
      if (activeConversation.current === startedIn) {
        setSendError({ message: errorMessage(err), text });
        setDraft(text);
      } else {
        toast.error(errorMessage(err));
      }
    } finally {
      setSending(false);
    }
  };

  const lastAssistantIndex = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) if (messages[i].role === "assistant") return i;
    return -1;
  }, [messages]);

  const regenerate = async () => {
    const target = messages[lastAssistantIndex];
    if (!target || regenerating) return;
    setRegenerating(true);
    try {
      if (target.id !== null) {
        const updated = await chatApi.regenerate(target.id);
        setMessages((prev) => prev.map((m, i) => (i === lastAssistantIndex ? updated : m)));
      } else {
        // Privacy mode: nothing is stored, so re-ask with the same local history.
        const question = messages[lastAssistantIndex - 1];
        const history = toHistory(messages.slice(0, lastAssistantIndex - 1));
        const res = await chatApi.send({ message: question.content, history });
        setMessages((prev) => prev.map((m, i) => (i === lastAssistantIndex ? res.assistant_message : m)));
      }
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setRegenerating(false);
    }
  };

  const feedback = async (msg: Msg, value: "up" | "down" | null) => {
    if (msg.id === null) return;
    try {
      const updated = await chatApi.feedback(msg.id, value);
      setMessages((prev) => prev.map((m) => (m.id === updated.id ? updated : m)));
      if (value) toast.info("Thanks — feedback saved.");
    } catch (err) {
      toast.error(errorMessage(err));
    }
  };

  const remember = async (msg: Msg) => {
    if (msg.id === null) return;
    try {
      await chatApi.remember(msg.id);
      setRemembered((s) => new Set(s).add(msg.id as number));
      toast.success("Saved as a conversation memory. You can review it in the Memory Inspector.");
    } catch (err) {
      toast.error(errorMessage(err));
    }
  };

  const confirmDelete = async () => {
    if (!deleting || deletingBusy) return;
    setDeletingBusy(true);
    try {
      await chatApi.removeConversation(deleting.id);
      toast.success("Conversation deleted.");
      if (deleting.id === conversationId) navigate("/app/chat");
      void conversations.reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setDeleting(null);
      setDeletingBusy(false);
    }
  };

  const saveTitle = async () => {
    const next = renaming?.trim();
    setRenaming(null);
    if (!next || conversationId === null || next === title) return;
    try {
      const updated = await chatApi.rename(conversationId, next);
      setTitle(updated.title);
      void conversations.reload();
    } catch (err) {
      toast.error(errorMessage(err));
    }
  };

  const newConversation = () => {
    setMessages([]);
    setTitle(null);
    setDraft("");
    navigate("/app/chat");
  };

  const sidebar = (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-line p-3">
        <p className="font-display font-semibold text-brown">Conversations</p>
        <Button size="sm" variant="accent" onClick={newConversation} icon={<MessageCirclePlus className="h-4 w-4" />}>
          New
        </Button>
      </div>
      <div className="scrollbar-thin flex-1 overflow-y-auto">
        {conversations.error ? (
          <div className="p-3 text-sm text-red-700">
            {conversations.error}{" "}
            <button type="button" className="underline" onClick={() => void conversations.reload()}>
              Retry
            </button>
          </div>
        ) : (
          <ConversationList
            conversations={conversations.data}
            activeId={conversationId}
            loading={conversations.loading}
            onDelete={setDeleting}
            onNavigate={() => setHistoryOpen(false)}
          />
        )}
      </div>
    </div>
  );

  return (
    <div className="-mx-4 -my-6 flex h-[calc(100dvh-57px)] sm:-mx-6 lg:-mx-10 lg:-my-10 lg:h-[100dvh]">
      <aside className="hidden w-72 shrink-0 border-r border-line bg-white/60 md:block" aria-label="Conversation history">
        {sidebar}
      </aside>

      <AnimatePresence>
        {historyOpen && (
          <div className="fixed inset-0 z-50 md:hidden">
            <motion.div className="absolute inset-0 bg-ink/40" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setHistoryOpen(false)} />
            <motion.aside
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "tween", duration: 0.2 }}
              className="absolute inset-y-0 right-0 w-80 max-w-[90%] bg-cream shadow-lift"
              aria-label="Conversation history"
            >
              <button type="button" onClick={() => setHistoryOpen(false)} className="absolute -left-10 top-3 rounded-lg bg-cream p-1.5 text-brown" aria-label="Close history">
                <X className="h-5 w-5" />
              </button>
              {sidebar}
            </motion.aside>
          </div>
        )}
      </AnimatePresence>

      <section className="flex min-w-0 flex-1 flex-col" aria-label="Mentor chat">
        <header className="flex items-center justify-between gap-3 border-b border-line bg-cream/80 px-4 py-3 backdrop-blur sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <Avatar name={mentorName} size="sm" />
            <div className="min-w-0">
              {renaming !== null ? (
                <form
                  className="flex items-center gap-1"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void saveTitle();
                  }}
                >
                  <label htmlFor="conv-title" className="sr-only">
                    Conversation title
                  </label>
                  <input
                    id="conv-title"
                    autoFocus
                    value={renaming}
                    maxLength={200}
                    onChange={(e) => setRenaming(e.target.value)}
                    onKeyDown={(e) => e.key === "Escape" && setRenaming(null)}
                    className="min-w-0 rounded-lg border border-line bg-white px-2 py-1 font-display text-base text-brown focus:border-mustard focus:outline-none"
                  />
                  <button type="submit" className="rounded-lg p-1.5 text-chocolate hover:bg-paper" aria-label="Save title">
                    <Check className="h-4 w-4" />
                  </button>
                </form>
              ) : (
                <div className="flex min-w-0 items-center gap-1">
                  <h1 className="truncate font-display text-lg font-semibold text-brown">{title ?? `Talk with ${mentorName}`}</h1>
                  {conversationId !== null && title && (
                    <button
                      type="button"
                      onClick={() => setRenaming(title)}
                      className="shrink-0 rounded-lg p-1 text-muted hover:bg-paper hover:text-chocolate"
                      aria-label="Rename conversation"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              )}
              <p className="flex flex-wrap items-center gap-2 text-xs text-muted">
                {overview.data?.ai.mode === "demo" ? "Demo mode · answers composed from your memories" : overview.data ? `Powered by ${overview.data.ai.model}` : " "}
              </p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {privacyMode && (
              <Badge tone="outline">
                <EyeOff className="h-3 w-3" aria-hidden /> Not saved
              </Badge>
            )}
            <button type="button" onClick={() => setHistoryOpen(true)} className="rounded-lg p-2 text-brown hover:bg-paper md:hidden" aria-label="Show conversation history">
              <History className="h-5 w-5" />
            </button>
          </div>
        </header>

        <div className="scrollbar-thin flex-1 overflow-y-auto px-4 py-6 sm:px-6" aria-live="polite" aria-busy={sending}>
          <div className="mx-auto max-w-3xl space-y-6">
            {loadingConv ? (
              <LoadingState label="Opening the conversation…" />
            ) : convError ? (
              <ErrorState message={convError} onRetry={() => conversationId && void loadConversation(conversationId)} />
            ) : messages.length === 0 && !sending ? (
              <div className="py-6 text-center sm:py-10">
                <div className="mx-auto mb-6 flex justify-center">
                  <StickyNote text="Ask me anything — I'll answer from what you've taught me." rotate={-3} className="w-56" />
                </div>
                <h2 className="text-2xl font-semibold">What's on your mind?</h2>
                <p className="mx-auto mt-2 max-w-md text-sm text-muted">
                  {mentorName} searches your knowledge and experiences before answering, cites what it used, and says so
                  when it has nothing relevant.
                </p>
                {privacyMode && (
                  <p className="mx-auto mt-3 max-w-md rounded-lg bg-paper px-3 py-2 text-xs text-chocolate">
                    Conversation saving is off — this chat lives only in this tab.
                  </p>
                )}
                <div className="mx-auto mt-6 grid max-w-2xl gap-2 sm:grid-cols-2">
                  {STARTERS.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => void send(s)}
                      className="card-paper p-3 text-left text-sm text-brown transition-transform hover:-translate-y-0.5 hover:border-gold"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((m, i) => (
                <ChatMessage
                  key={m.id ?? `tmp-${i}`}
                  message={m}
                  mentorName={mentorName}
                  showSources={showSources}
                  isLastAssistant={i === lastAssistantIndex && !sending}
                  busy={regenerating}
                  onRegenerate={() => void regenerate()}
                  onFeedback={(f) => void feedback(m, f)}
                  onRemember={() => void remember(m)}
                  remembered={Boolean(m.remembered) || (m.id !== null && remembered.has(m.id))}
                />
              ))
            )}
            <AnimatePresence>{sending && <TypingIndicator mentorName={mentorName} />}</AnimatePresence>
            {sendError && (
              <div role="alert" className="flex flex-wrap items-center gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                <span className="flex-1">{sendError.message}</span>
                <Button size="sm" variant="secondary" onClick={() => void send(sendError.text)} icon={<RefreshCw className="h-3.5 w-3.5" />}>
                  Retry
                </Button>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        <div className="border-t border-line bg-cream/80 px-4 py-3 backdrop-blur sm:px-6">
          <div className="mx-auto max-w-3xl">
            <ChatInput value={draft} onChange={setDraft} onSend={() => void send()} disabled={sending || loadingConv} />
            <p className="mt-1.5 text-center text-[11px] text-muted">
              Mentoring perspectives, not professional advice. Enter to send · Shift+Enter for a new line.
            </p>
          </div>
        </div>
      </section>

      <ConfirmDialog
        open={!!deleting}
        title="Delete this conversation?"
        message={<>All messages in “{deleting?.title}” will be deleted. Saved conversation memories are kept.</>}
        onConfirm={confirmDelete}
        loading={deletingBusy}
        onClose={() => setDeleting(null)}
      />
    </div>
  );
}
