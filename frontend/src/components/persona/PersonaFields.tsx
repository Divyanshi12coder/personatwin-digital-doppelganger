import { Check } from "lucide-react";
import { useId } from "react";
import { Slider, Textarea } from "@/components/ui/Field";
import { TagInput } from "@/components/ui/TagInput";
import type { OptionItem, PersonaOptionKey, Personality } from "@/types/api";
import { cn, humanize } from "@/utils/format";

export const DEFAULT_PERSONALITY: Personality = {
  communication_style: "warm",
  tone: "encouraging",
  teaching_approach: "examples_first",
  decision_style: "analytical",
  encouragement_style: "celebrate_progress",
  response_length: "balanced",
  formality: 40,
  directness: 60,
  warmth: 70,
  humor: 30,
  values: [],
  signature_phrases: [],
  philosophy_encouragement: "",
  philosophy_mistakes: "",
  philosophy_decisions: "",
  philosophy_teaching: "",
  boundaries: "",
};

export const PERSONA_LABELS: Record<PersonaOptionKey, string> = {
  communication_style: "Communication style",
  tone: "Tone",
  teaching_approach: "Teaching approach",
  decision_style: "Decision style",
  encouragement_style: "Encouragement style",
  response_length: "Preferred response length",
};

const VALUE_SUGGESTIONS = ["Curiosity", "Honesty", "Craftsmanship", "Kindness", "Courage", "Discipline", "Growth", "Integrity"];

/** Accessible radio-card group for one persona dimension. */
export function OptionCards({
  label,
  options,
  value,
  onChange,
  columns = 2,
}: {
  label: string;
  options: OptionItem[];
  value: string;
  onChange: (v: string) => void;
  columns?: 2 | 3;
}) {
  const name = useId();
  return (
    <fieldset>
      <legend className="mb-2 text-sm font-semibold text-brown">{label}</legend>
      <div className={cn("grid gap-2", columns === 3 ? "sm:grid-cols-3" : "sm:grid-cols-2")}>
        {options.map((o) => {
          const checked = o.value === value;
          return (
            <label
              key={o.value}
              className={cn(
                "relative flex cursor-pointer gap-3 rounded-xl border bg-white p-3 text-left transition-colors focus-within:ring-2 focus-within:ring-mustard/50",
                checked ? "border-mustard bg-softgold/40 shadow-paper" : "border-line hover:border-chocolate/30",
              )}
            >
              <input
                type="radio"
                name={name}
                value={o.value}
                checked={checked}
                onChange={() => onChange(o.value)}
                className="sr-only"
              />
              <span
                className={cn(
                  "mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full border",
                  checked ? "border-chocolate bg-chocolate text-cream" : "border-line",
                )}
                aria-hidden
              >
                {checked && <Check className="h-3 w-3" />}
              </span>
              <span>
                <span className="block text-sm font-semibold text-brown">{humanize(o.value)}</span>
                <span className="block text-xs text-muted">{o.description}</span>
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

const SLIDERS: { key: "formality" | "directness" | "warmth" | "humor"; label: string; low: string; high: string }[] = [
  { key: "formality", label: "Formality", low: "Casual", high: "Formal" },
  { key: "directness", label: "Directness", low: "Gentle", high: "Direct" },
  { key: "warmth", label: "Warmth", low: "Reserved", high: "Warm" },
  { key: "humor", label: "Humor", low: "Serious", high: "Playful" },
];

export function StyleFields({
  value,
  onChange,
  options,
  keys,
}: {
  value: Personality;
  onChange: (p: Personality) => void;
  options: Record<PersonaOptionKey, OptionItem[]>;
  keys?: PersonaOptionKey[];
}) {
  const shown = keys ?? (Object.keys(PERSONA_LABELS) as PersonaOptionKey[]);
  return (
    <div className="space-y-6">
      {shown.map((k) => (
        <OptionCards
          key={k}
          label={PERSONA_LABELS[k]}
          options={options[k] ?? []}
          value={value[k]}
          onChange={(v) => onChange({ ...value, [k]: v })}
          columns={k === "response_length" ? 3 : 2}
        />
      ))}
    </div>
  );
}

export function SliderFields({ value, onChange }: { value: Personality; onChange: (p: Personality) => void }) {
  return (
    <div className="grid gap-6 sm:grid-cols-2">
      {SLIDERS.map((s) => (
        <Slider
          key={s.key}
          label={s.label}
          low={s.low}
          high={s.high}
          value={value[s.key]}
          onChange={(v) => onChange({ ...value, [s.key]: v })}
        />
      ))}
    </div>
  );
}

export function ValuesFields({ value, onChange }: { value: Personality; onChange: (p: Personality) => void }) {
  return (
    <div className="space-y-5">
      <TagInput
        label="Core values"
        value={value.values}
        onChange={(values) => onChange({ ...value, values })}
        suggestions={VALUE_SUGGESTIONS}
        placeholder="e.g. Curiosity"
        hint="What you care about most when giving advice."
      />
      <TagInput
        label="Signature phrases (optional)"
        value={value.signature_phrases}
        onChange={(signature_phrases) => onChange({ ...value, signature_phrases })}
        placeholder="e.g. Small experiments beat big guesses."
        hint="Things you often say. Your twin uses them sparingly."
        max={8}
      />
    </div>
  );
}

export function PhilosophyFields({ value, onChange }: { value: Personality; onChange: (p: Personality) => void }) {
  const field = (key: keyof Personality, label: string, placeholder: string) => (
    <Textarea
      label={label}
      rows={3}
      maxLength={2000}
      placeholder={placeholder}
      value={value[key] as string}
      onChange={(e) => onChange({ ...value, [key]: e.target.value })}
    />
  );
  return (
    <div className="grid gap-5 md:grid-cols-2">
      {field(
        "philosophy_encouragement",
        "How do you encourage people?",
        "I point out concrete progress, even small wins, before suggesting what's next…",
      )}
      {field("philosophy_mistakes", "How do you handle mistakes?", "Mistakes are data. We look at what happened without blame…")}
      {field(
        "philosophy_decisions",
        "How do you approach difficult decisions?",
        "I separate reversible from irreversible choices and test the reversible ones quickly…",
      )}
      {field("philosophy_teaching", "How do you teach?", "Show one worked example, then let the person try while I watch…")}
      <div className="md:col-span-2">
        {field("boundaries", "Boundaries (optional)", "Topics your twin should avoid or redirect, e.g. medical questions.")}
      </div>
    </div>
  );
}
