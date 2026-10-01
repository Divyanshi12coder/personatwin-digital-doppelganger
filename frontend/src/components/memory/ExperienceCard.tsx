import { AnimatePresence, motion } from "framer-motion";
import { CalendarDays, ChevronDown, Pencil, Star, Trash2 } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/Feedback";
import type { Experience } from "@/types/api";
import { cn, formatDate, humanize } from "@/utils/format";

export function ExperienceCard({
  exp,
  typeLabel,
  onEdit,
  onDelete,
}: {
  exp: Experience;
  typeLabel: string;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const [open, setOpen] = useState(false);
  const details = [
    ["Situation", exp.situation],
    ["What happened", exp.what_happened],
    ["What I'd do differently", exp.do_differently],
  ].filter(([, v]) => v);

  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="card-paper ruled relative overflow-hidden pl-14 pr-5 py-5 sm:pr-6"
    >
      <div className="absolute left-4 top-5 flex flex-col items-center gap-0.5" aria-label={`Importance ${exp.importance} of 5`}>
        {Array.from({ length: 5 }).map((_, i) => (
          <Star
            key={i}
            className={cn("h-3.5 w-3.5", i < exp.importance ? "fill-mustard text-mustard" : "text-line")}
            aria-hidden
          />
        ))}
      </div>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="mb-1 flex flex-wrap items-center gap-2">
            <Badge tone="brown">{typeLabel}</Badge>
            {!exp.indexed && <Badge tone="red">Not indexed</Badge>}
            <span className="flex items-center gap-1 text-xs text-muted">
              <CalendarDays className="h-3.5 w-3.5" aria-hidden />
              {[exp.occurred_on ? formatDate(exp.occurred_on) : null, exp.context || null].filter(Boolean).join(" · ") ||
                `Added ${formatDate(exp.created_at)}`}
            </span>
          </div>
          <h3 className="text-xl font-semibold">{exp.title}</h3>
        </div>
        <div className="flex gap-1">
          <button type="button" onClick={onEdit} className="rounded-lg p-1.5 text-chocolate hover:bg-paper" aria-label={`Edit ${exp.title}`}>
            <Pencil className="h-4 w-4" />
          </button>
          <button type="button" onClick={onDelete} className="rounded-lg p-1.5 text-red-700 hover:bg-red-50" aria-label={`Delete ${exp.title}`}>
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {exp.lesson_learned && (
        <div className="mt-3 rounded-lg border-l-4 border-mustard bg-softgold/50 px-4 py-2.5">
          <p className="font-hand text-lg leading-none text-chocolate">What I learned</p>
          <p className="mt-1 text-sm text-ink/85">{exp.lesson_learned}</p>
        </div>
      )}

      <AnimatePresence initial={false}>
        {open && (
          <motion.dl
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="space-y-3 pt-4">
              {details.map(([label, value]) => (
                <div key={label}>
                  <dt className="text-xs font-semibold uppercase tracking-wider text-muted">{label}</dt>
                  <dd className="mt-0.5 whitespace-pre-line text-sm text-ink/85">{value}</dd>
                </div>
              ))}
            </div>
          </motion.dl>
        )}
      </AnimatePresence>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-1">
          {exp.tags.map((t) => (
            <span key={t} className="chip">
              #{t}
            </span>
          ))}
        </div>
        {details.length > 0 && (
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            aria-expanded={open}
            className="inline-flex items-center gap-1 text-xs font-semibold text-chocolate hover:underline"
          >
            {open ? "Hide the story" : "Read the full story"}
            <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", open && "rotate-180")} aria-hidden />
          </button>
        )}
      </div>
    </motion.article>
  );
}

export const experienceTypeLabel = (value: string, types?: { value: string; description: string }[]) =>
  types?.find((t) => t.value === value)?.description ?? humanize(value);
