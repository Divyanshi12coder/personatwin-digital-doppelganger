import { X } from "lucide-react";
import { useId, useState, type KeyboardEvent } from "react";

interface TagInputProps {
  label: string;
  value: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  hint?: string;
  max?: number;
  suggestions?: string[];
  lowercase?: boolean;
}

/** Chip-style list input: Enter or comma adds, Backspace removes the last chip. */
export function TagInput({
  label,
  value,
  onChange,
  placeholder = "Type and press Enter",
  hint,
  max = 12,
  suggestions = [],
  lowercase = false,
}: TagInputProps) {
  const id = useId();
  const [draft, setDraft] = useState("");

  const add = (raw: string) => {
    const tag = (lowercase ? raw.toLowerCase() : raw).replace(/\s+/g, " ").trim().replace(/^#/, "");
    if (!tag || value.length >= max) return;
    if (value.some((v) => v.toLowerCase() === tag.toLowerCase())) return;
    onChange([...value, tag.slice(0, 60)]);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      add(draft);
      setDraft("");
    } else if (e.key === "Backspace" && !draft && value.length) {
      onChange(value.slice(0, -1));
    }
  };

  const unused = suggestions.filter((s) => !value.some((v) => v.toLowerCase() === s.toLowerCase()));

  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-sm font-medium text-brown">
        {label}
      </label>
      <div className="flex min-h-[44px] flex-wrap items-center gap-1.5 rounded-xl border border-line bg-white px-2.5 py-2 focus-within:border-mustard focus-within:ring-2 focus-within:ring-mustard/40">
        {value.map((tag) => (
          <span key={tag} className="chip bg-softgold/70">
            {tag}
            <button
              type="button"
              onClick={() => onChange(value.filter((t) => t !== tag))}
              className="rounded-full p-0.5 hover:bg-white"
              aria-label={`Remove ${tag}`}
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
        <input
          id={id}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          onBlur={() => {
            if (draft.trim()) {
              add(draft);
              setDraft("");
            }
          }}
          placeholder={value.length ? "" : placeholder}
          className="min-w-[8rem] flex-1 bg-transparent px-1 py-0.5 text-sm outline-none placeholder:text-muted/70"
          aria-describedby={hint ? `${id}-hint` : undefined}
        />
      </div>
      {unused.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1" aria-label={`Suggestions for ${label}`}>
          {unused.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => add(s)}
              className="rounded-full border border-dashed border-chocolate/30 px-2.5 py-0.5 text-xs text-chocolate hover:border-mustard hover:bg-softgold/50"
            >
              + {s}
            </button>
          ))}
        </div>
      )}
      {hint && (
        <p id={`${id}-hint`} className="text-xs text-muted">
          {hint}
        </p>
      )}
    </div>
  );
}
