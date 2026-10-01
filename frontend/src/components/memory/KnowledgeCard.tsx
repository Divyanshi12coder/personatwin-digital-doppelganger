import { motion } from "framer-motion";
import { FileText, Globe, Layers, NotebookText, Pencil, StickyNote, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/Feedback";
import type { KnowledgeItem } from "@/types/api";
import { formatDate, humanize, pluralize } from "@/utils/format";

const SOURCE_ICONS = { text: NotebookText, note: StickyNote, document: FileText, url: Globe } as const;

export function KnowledgeCard({
  item,
  onEdit,
  onDelete,
  index = 0,
}: {
  item: KnowledgeItem;
  onEdit: () => void;
  onDelete: () => void;
  index?: number;
}) {
  const Icon = SOURCE_ICONS[item.source_type] ?? NotebookText;
  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ delay: Math.min(index * 0.03, 0.3) }}
      className="card-paper group flex flex-col p-5"
    >
      <div className="flex items-start justify-between gap-3">
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-softgold text-chocolate">
          <Icon className="h-4 w-4" aria-hidden />
        </span>
        <div className="flex flex-wrap justify-end gap-1.5">
          <Badge tone="gold">{humanize(item.category)}</Badge>
          {!item.indexed && <Badge tone="red">Not indexed</Badge>}
        </div>
      </div>
      <h3 className="mt-3 line-clamp-2 text-lg font-semibold">{item.title}</h3>
      <p className="mt-1.5 line-clamp-3 flex-1 text-sm text-ink/75">{item.content}</p>
      {item.tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {item.tags.map((t) => (
            <span key={t} className="chip">
              #{t}
            </span>
          ))}
        </div>
      )}
      <div className="mt-4 flex items-center justify-between border-t border-dashed border-line pt-3 text-xs text-muted">
        <span className="flex items-center gap-1.5" title={item.source}>
          <Layers className="h-3.5 w-3.5" aria-hidden /> {pluralize(item.chunk_count, "chunk")} · {formatDate(item.created_at)}
        </span>
        <div className="flex gap-1">
          <button
            type="button"
            onClick={onEdit}
            className="rounded-lg p-1.5 text-chocolate hover:bg-paper"
            aria-label={`Edit ${item.title}`}
          >
            <Pencil className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={onDelete}
            className="rounded-lg p-1.5 text-red-700 hover:bg-red-50"
            aria-label={`Delete ${item.title}`}
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
    </motion.article>
  );
}
