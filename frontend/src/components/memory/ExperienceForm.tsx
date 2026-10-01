import { Save, Star } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Input, Select, Textarea } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { TagInput } from "@/components/ui/TagInput";
import { useOptions } from "@/context/OptionsContext";
import { errorMessage } from "@/services/api";
import { experienceApi } from "@/services/endpoints";
import type { Experience, ExperienceInput } from "@/types/api";
import { cn } from "@/utils/format";

const EMPTY: ExperienceInput = {
  title: "",
  experience_type: "lesson",
  situation: "",
  what_happened: "",
  lesson_learned: "",
  do_differently: "",
  context: "",
  occurred_on: null,
  importance: 3,
  tags: [],
};

export function ExperienceForm({
  open,
  onClose,
  onSaved,
  editing,
}: {
  open: boolean;
  onClose: () => void;
  onSaved: (exp: Experience, created: boolean) => void;
  editing?: Experience | null;
}) {
  const { options } = useOptions();
  const [form, setForm] = useState<ExperienceInput>(EMPTY);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setError(null);
    setForm(editing ? { ...EMPTY, ...editing } : EMPTY);
  }, [open, editing]);

  const set = <K extends keyof ExperienceInput>(key: K, value: ExperienceInput[K]) => setForm((f) => ({ ...f, [key]: value }));
  const today = new Date().toISOString().slice(0, 10);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!form.title.trim()) return setError("Give the experience a title.");
    if (![form.situation, form.what_happened, form.lesson_learned].some((v) => v.trim()))
      return setError("Describe the situation, what happened, or what you learned.");
    setSaving(true);
    try {
      const payload: ExperienceInput = { ...form, occurred_on: form.occurred_on || null };
      const saved = editing ? await experienceApi.update(editing.id, payload) : await experienceApi.create(payload);
      onSaved(saved, !editing);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="xl"
      title={editing ? "Edit experience" : "Record an experience"}
      description="Specific, honest stories make the best mentoring. Only what you write here can be told as a personal memory."
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" form="experience-form" loading={saving} icon={<Save className="h-4 w-4" />}>
            {editing ? "Save changes" : "Save experience"}
          </Button>
        </>
      }
    >
      <form id="experience-form" onSubmit={submit} className="space-y-5" noValidate>
        {error && (
          <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}
        <div className="grid gap-4 md:grid-cols-[1fr_220px]">
          <Input label="Title" value={form.title} onChange={(e) => set("title", e.target.value)} maxLength={200} required placeholder="The time I…" />
          <Select label="Kind of experience" value={form.experience_type} onChange={(e) => set("experience_type", e.target.value)}>
            {(options?.experience_types ?? []).map((t) => (
              <option key={t.value} value={t.value}>
                {t.description}
              </option>
            ))}
          </Select>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <Textarea label="Situation" rows={4} value={form.situation} onChange={(e) => set("situation", e.target.value)} placeholder="Where were you, what was at stake?" maxLength={5000} />
          <Textarea label="What happened" rows={4} value={form.what_happened} onChange={(e) => set("what_happened", e.target.value)} placeholder="What did you do, and how did it play out?" maxLength={5000} />
          <Textarea label="What I learned" rows={4} value={form.lesson_learned} onChange={(e) => set("lesson_learned", e.target.value)} placeholder="The lesson you'd pass on." maxLength={5000} />
          <Textarea label="What I would do differently" rows={4} value={form.do_differently} onChange={(e) => set("do_differently", e.target.value)} placeholder="With hindsight…" maxLength={5000} />
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <Input label="Context" value={form.context} onChange={(e) => set("context", e.target.value)} maxLength={200} placeholder="e.g. first job, 2019, London" />
          <Input label="When (optional)" type="date" max={today} value={form.occurred_on ?? ""} onChange={(e) => set("occurred_on", e.target.value || null)} />
          <fieldset>
            <legend className="mb-1.5 text-sm font-medium text-brown">Importance</legend>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => set("importance", n)}
                  aria-label={`Importance ${n} of 5`}
                  aria-pressed={form.importance === n}
                  className="rounded-lg p-1.5 hover:bg-softgold/50"
                >
                  <Star className={cn("h-6 w-6", n <= form.importance ? "fill-mustard text-mustard" : "text-line")} />
                </button>
              ))}
            </div>
          </fieldset>
        </div>
        <TagInput label="Tags" value={form.tags} onChange={(tags) => set("tags", tags)} lowercase placeholder="e.g. career change" />
      </form>
    </Modal>
  );
}
