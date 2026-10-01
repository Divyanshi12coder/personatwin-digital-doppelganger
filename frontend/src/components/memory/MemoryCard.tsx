import { motion } from "framer-motion";
import { BookOpen, Brain, MessageCircle, NotebookPen, Pencil, Trash2 } from "lucide-react";
import type { MemoryItem, MemoryType } from "@/types/api";
import { Badge } from "@/components/ui/Feedback";
import { formatDate, humanize, topicLabel } from "@/utils/format";

export const MEMORY_META: Record<MemoryType, { label: string; icon: typeof BookOpen; kind: string }> = {
  knowledge: { label: "Knowledge", icon: BookOpen, kind: "Long-term semantic" },
  experience: { label: "Experience", icon: NotebookPen, kind: "Episodic" },
  preference: { label: "Preference", icon: Brain, kind: "Persona" },
  conversation: { label: "Conversation", icon: MessageCircle, kind: "Saved exchange" },
};

export function MemoryCard({
  item,
  onEdit,
  onDelete,
  index = 0,
}: {
  item: MemoryItem;
  onEdit: () => void;
  onDelete?: () => void;
  index?: number;
}) {
  const meta = MEMORY_META[item.type];
  const category = item.type === "conversation" ? topicLabel(item.category) : humanize(item.category);
  return (
    <motion.li
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ delay: Math.min(index * 0.025, 0.25) }}
      className="card-paper flex gap-4 p-4 sm:p-5"
    >
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-softgold text-chocolate">
        <meta.icon className="h-5 w-5" aria-hidden />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge tone="brown">{meta.label}</Badge>
          <Badge>{category}</Badge>
          {!item.indexed && <Badge tone="red">Not indexed</Badge>}
        </div>
        <h3 className="mt-1.5 text-base font-semibold sm:text-lg">{item.title}</h3>
        <p className="mt-1 line-clamp-2 text-sm text-ink/75">{item.snippet}</p>
        <dl className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
          <div>
            <dt className="sr-only">Date</dt>
            <dd>{formatDate(item.date)}</dd>
          </div>
          <div className="max-w-[16rem] truncate">
            <dt className="inline">Source: </dt>
            <dd className="inline">{item.source}</dd>
          </div>
          {item.tags.length > 0 && (
            <div>
              <dt className="sr-only">Tags</dt>
              <dd>{item.tags.map((t) => `#${t}`).join(" ")}</dd>
            </div>
          )}
        </dl>
        {item.relevance !== null && (
          <div className="mt-2 flex max-w-xs items-center gap-2" aria-label={`Relevance ${item.relevance.toFixed(2)}`}>
            <span className="text-xs text-muted">Relevance</span>
            <div className="h-1.5 flex-1 rounded-full bg-line">
              <motion.div
                className="h-1.5 rounded-full bg-mustard"
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(100, Math.max(3, item.relevance * 100))}%` }}
              />
            </div>
            <span className="text-xs tabular-nums text-chocolate">{item.relevance.toFixed(2)}</span>
          </div>
        )}
      </div>
      <div className="flex shrink-0 flex-col gap-1">
        <button type="button" onClick={onEdit} className="rounded-lg p-1.5 text-chocolate hover:bg-paper" aria-label={`Edit ${item.title}`}>
          <Pencil className="h-4 w-4" />
        </button>
        {onDelete && (
          <button type="button" onClick={onDelete} className="rounded-lg p-1.5 text-red-700 hover:bg-red-50" aria-label={`Delete ${item.title}`}>
            <Trash2 className="h-4 w-4" />
          </button>
        )}
      </div>
    </motion.li>
  );
}
