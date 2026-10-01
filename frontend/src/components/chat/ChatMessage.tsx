import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  BookOpen,
  Bookmark,
  Check,
  ChevronDown,
  Copy,
  MessageCircle,
  NotebookPen,
  RefreshCw,
  ThumbsDown,
  ThumbsUp,
  Workflow,
} from "lucide-react";
import { useState } from "react";
import { Avatar, Badge } from "@/components/ui/Feedback";
import type { ChatMessage as Msg, Source } from "@/types/api";
import { cn, formatTime, topicLabel } from "@/utils/format";
import { RichText } from "./RichText";

const SOURCE_ICON = { knowledge: BookOpen, experience: NotebookPen, conversation: MessageCircle } as const;
const SOURCE_LABEL = { knowledge: "Knowledge", experience: "Experience", conversation: "Past conversation" } as const;
const GROUNDING = {
  grounded: { tone: "green" as const, label: "Grounded in your memories" },
  partial: { tone: "gold" as const, label: "Memories consulted, not cited" },
  ungrounded: { tone: "default" as const, label: "General guidance — no matching memories" },
};
const STEP_LABELS: Record<string, string> = {
  understand: "Understand the question",
  retrieve: "Retrieve memories",
  persona: "Load persona",
  assemble: "Assemble context",
  prompt: "Build prompt",
  generate: "Generate",
  validate: "Validate response",
};

function SourceRow({ s, highlighted }: { s: Source; highlighted: boolean }) {
  const Icon = SOURCE_ICON[s.source_type];
  return (
    <li
      id={`src-${s.label}`}
      className={cn(
        "rounded-xl border bg-white p-3 transition-shadow",
        highlighted ? "border-mustard shadow-paper ring-2 ring-mustard/40" : "border-line",
      )}
    >
      <div className="flex items-start gap-2.5">
        <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-softgold text-chocolate">
          <Icon className="h-3.5 w-3.5" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="rounded bg-brown px-1.5 text-[11px] font-semibold text-cream">{s.label}</span>
            <span className="text-xs text-muted">{SOURCE_LABEL[s.source_type]}</span>
            {s.cited && <Badge tone="green">cited</Badge>}
          </div>
          <p className="mt-1 truncate text-sm font-medium text-brown">{s.title}</p>
          <p className="mt-0.5 line-clamp-2 text-xs text-muted">{s.snippet}</p>
          <div className="mt-2 flex items-center gap-2" aria-label={`Relevance ${Math.round(s.score * 100)} percent`}>
            <div className="h-1 flex-1 rounded-full bg-line">
              <div className="h-1 rounded-full bg-mustard" style={{ width: `${Math.min(100, Math.max(4, s.score * 100))}%` }} />
            </div>
            <span className="text-[11px] tabular-nums text-muted">{s.score.toFixed(2)}</span>
          </div>
        </div>
      </div>
    </li>
  );
}

interface Props {
  message: Msg;
  mentorName: string;
  showSources: boolean;
  isLastAssistant: boolean;
  busy?: boolean;
  onRegenerate?: () => void;
  onFeedback?: (f: "up" | "down" | null) => void;
  onRemember?: () => void;
  remembered?: boolean;
}

export function ChatMessage({
  message,
  mentorName,
  showSources,
  isLastAssistant,
  busy,
  onRegenerate,
  onFeedback,
  onRemember,
  remembered,
}: Props) {
  const [copied, setCopied] = useState(false);
  const [openPanel, setOpenPanel] = useState<"sources" | "trace" | null>(null);
  const [highlight, setHighlight] = useState<string | null>(null);

  if (message.role === "user") {
    return (
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex justify-end">
        <div className="max-w-[85%] sm:max-w-[75%]">
          <div className="rounded-2xl rounded-br-md bg-brown px-4 py-3 text-[15px] leading-relaxed text-cream shadow-paper">
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
          <p className="mt-1 text-right text-[11px] text-muted">{formatTime(message.created_at)}</p>
        </div>
      </motion.div>
    );
  }

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  };

  const onCite = (label: string) => {
    setOpenPanel("sources");
    setHighlight(label);
    window.setTimeout(() => document.getElementById(`src-${label}`)?.scrollIntoView({ block: "nearest", behavior: "smooth" }), 60);
  };

  const grounding = message.grounding ? GROUNDING[message.grounding] : null;
  const notice = message.trace?.notice;
  const persisted = message.id !== null;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex gap-3">
      <Avatar name={mentorName} size="sm" className="mt-1 hidden sm:grid" />
      <div className="min-w-0 max-w-full flex-1 sm:max-w-[85%]">
        <div className="card-paper rounded-tl-md px-4 py-4 sm:px-5">
          {notice && (
            <div className="mb-3 flex gap-2 rounded-lg bg-softgold/60 px-3 py-2 text-xs text-brown">
              <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden /> {notice}
            </div>
          )}
          <RichText text={message.content} onCite={showSources ? onCite : undefined} />
        </div>

        <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-muted">
          <span>{formatTime(message.created_at)}</span>
          {message.topic && message.topic !== "general" && <span>· {topicLabel(message.topic)}</span>}
          {message.provider === "demo" && <span>· demo composer</span>}
          {message.latency_ms !== null && <span>· {(message.latency_ms / 1000).toFixed(1)}s</span>}
          {grounding && <Badge tone={grounding.tone}>{grounding.label}</Badge>}
        </div>

        <div className="mt-2 flex flex-wrap items-center gap-1">
          {showSources && message.sources.length > 0 && (
            <button
              type="button"
              onClick={() => setOpenPanel((p) => (p === "sources" ? null : "sources"))}
              aria-expanded={openPanel === "sources"}
              className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-chocolate hover:bg-softgold/50"
            >
              <BookOpen className="h-3.5 w-3.5" aria-hidden /> {message.sources.length} memories used
              <ChevronDown className={cn("h-3 w-3 transition-transform", openPanel === "sources" && "rotate-180")} aria-hidden />
            </button>
          )}
          {message.trace?.steps && (
            <button
              type="button"
              onClick={() => setOpenPanel((p) => (p === "trace" ? null : "trace"))}
              aria-expanded={openPanel === "trace"}
              className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-chocolate hover:bg-softgold/50"
            >
              <Workflow className="h-3.5 w-3.5" aria-hidden /> How this was made
            </button>
          )}
          <span className="mx-1 h-4 w-px bg-line" aria-hidden />
          <button type="button" onClick={() => void copy()} className="rounded-lg p-1.5 text-muted hover:bg-paper hover:text-chocolate" aria-label="Copy response">
            {copied ? <Check className="h-4 w-4 text-emerald-700" /> : <Copy className="h-4 w-4" />}
          </button>
          {isLastAssistant && onRegenerate && (
            <button
              type="button"
              onClick={onRegenerate}
              disabled={busy}
              className="rounded-lg p-1.5 text-muted hover:bg-paper hover:text-chocolate disabled:opacity-50"
              aria-label="Regenerate response"
              title="Regenerate"
            >
              <RefreshCw className={cn("h-4 w-4", busy && "animate-spin")} />
            </button>
          )}
          {persisted && onFeedback && (
            <>
              <button
                type="button"
                onClick={() => onFeedback(message.feedback === "up" ? null : "up")}
                aria-pressed={message.feedback === "up"}
                className={cn("rounded-lg p-1.5 hover:bg-paper", message.feedback === "up" ? "text-emerald-700" : "text-muted")}
                aria-label="Helpful"
              >
                <ThumbsUp className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => onFeedback(message.feedback === "down" ? null : "down")}
                aria-pressed={message.feedback === "down"}
                className={cn("rounded-lg p-1.5 hover:bg-paper", message.feedback === "down" ? "text-red-700" : "text-muted")}
                aria-label="Not helpful"
              >
                <ThumbsDown className="h-4 w-4" />
              </button>
            </>
          )}
          {persisted && onRemember && (
            <button
              type="button"
              onClick={onRemember}
              disabled={remembered}
              className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-chocolate hover:bg-softgold/50 disabled:opacity-60"
              title="Save this exchange as a conversation memory"
            >
              <Bookmark className={cn("h-3.5 w-3.5", remembered && "fill-chocolate")} aria-hidden />
              {remembered ? "Remembered" : "Remember this"}
            </button>
          )}
        </div>

        <AnimatePresence initial={false}>
          {openPanel === "sources" && (
            <motion.ul
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mt-2 grid gap-2 overflow-hidden sm:grid-cols-2"
              aria-label="Memories used for this answer"
            >
              {message.sources.map((s) => (
                <SourceRow key={s.label} s={s} highlighted={highlight === s.label} />
              ))}
            </motion.ul>
          )}
          {openPanel === "trace" && message.trace && (
            <motion.ol
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mt-2 overflow-hidden rounded-xl border border-line bg-white p-3"
              aria-label="Pipeline steps"
            >
              {message.trace.steps.map((step, i) => (
                <li key={step.step} className="flex items-start gap-3 py-1.5">
                  <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-softgold text-[10px] font-bold text-brown">
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold text-brown">{STEP_LABELS[step.step] ?? step.step}</p>
                    <p className="text-xs text-muted">{step.detail}</p>
                  </div>
                  <span className="text-[11px] tabular-nums text-muted">{step.ms} ms</span>
                </li>
              ))}
            </motion.ol>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

/** Shown while the backend runs the pipeline. Purely an activity indicator — real step data arrives with the reply. */
export function TypingIndicator({ mentorName }: { mentorName: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex gap-3" role="status" aria-live="polite">
      <Avatar name={mentorName} size="sm" className="mt-1 hidden sm:grid" />
      <div className="card-paper inline-flex items-center gap-3 px-4 py-3">
        <div className="flex gap-1" aria-hidden>
          {[0, 1, 2].map((i) => (
            <span key={i} className="h-2 w-2 animate-blink rounded-full bg-mustard" style={{ animationDelay: `${i * 0.16}s` }} />
          ))}
        </div>
        <span className="font-hand text-lg text-chocolate">{mentorName} is looking through your notes…</span>
      </div>
    </motion.div>
  );
}
