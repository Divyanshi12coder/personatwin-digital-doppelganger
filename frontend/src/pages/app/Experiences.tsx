import { AnimatePresence } from "framer-motion";
import { NotebookPen, Plus, Search } from "lucide-react";
import { useState } from "react";
import { ExperienceCard, experienceTypeLabel } from "@/components/memory/ExperienceCard";
import { ExperienceForm } from "@/components/memory/ExperienceForm";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState, PageHeader, Skeleton } from "@/components/ui/Feedback";
import { Input } from "@/components/ui/Field";
import { ConfirmDialog } from "@/components/ui/Modal";
import { visuals } from "@/config/visuals";
import { useOptions } from "@/context/OptionsContext";
import { useToast } from "@/context/ToastContext";
import { useAsync, useDebounce, useDocumentTitle } from "@/hooks/useAsync";
import { errorMessage } from "@/services/api";
import { experienceApi } from "@/services/endpoints";
import type { Experience } from "@/types/api";
import { cn, pluralize } from "@/utils/format";

export default function ExperiencesPage() {
  useDocumentTitle("Experiences");
  const toast = useToast();
  const { options } = useOptions();
  const [q, setQ] = useState("");
  const [type, setType] = useState("");
  const debouncedQ = useDebounce(q, 300);
  const list = useAsync(() => experienceApi.list({ q: debouncedQ, experience_type: type }), [debouncedQ, type]);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Experience | null>(null);
  const [deleting, setDeleting] = useState<Experience | null>(null);
  const [busy, setBusy] = useState(false);

  const onSaved = (_: Experience, created: boolean) => {
    setFormOpen(false);
    setEditing(null);
    toast.success(created ? "Experience saved to episodic memory." : "Experience updated and re-indexed.");
    void list.reload();
  };

  const confirmDelete = async () => {
    if (!deleting) return;
    setBusy(true);
    try {
      await experienceApi.remove(deleting.id);
      list.setData((prev) => prev?.filter((e) => e.id !== deleting.id) ?? prev);
      toast.success("Experience deleted.");
      setDeleting(null);
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const types = options?.experience_types ?? [];

  return (
    <div>
      <PageHeader
        eyebrow="Episodic memory"
        title="Experiences"
        description="The stories behind your advice — successes, failures, decisions and teaching moments. Your mentor only speaks of these as personal memories."
        actions={
          <Button
            onClick={() => {
              setEditing(null);
              setFormOpen(true);
            }}
            icon={<Plus className="h-4 w-4" />}
          >
            Record an experience
          </Button>
        }
      />

      <div className="mb-6 space-y-3">
        <div className="relative max-w-md">
          <Search className="pointer-events-none absolute left-3 top-[38px] h-4 w-4 text-muted" aria-hidden />
          <Input label="Search experiences" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search your stories" className="pl-9" />
        </div>
        <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by kind">
          {[{ value: "", description: "All" }, ...types].map((t) => (
            <button
              key={t.value || "all"}
              type="button"
              onClick={() => setType(t.value)}
              aria-pressed={type === t.value}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                type === t.value ? "border-brown bg-brown text-cream" : "border-line bg-white text-chocolate hover:border-chocolate/40",
              )}
            >
              {t.description}
            </button>
          ))}
        </div>
      </div>

      {list.error ? (
        <ErrorState message={list.error} onRetry={list.reload} />
      ) : list.loading && !list.data ? (
        <div className="space-y-4">
          {[0, 1].map((i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      ) : list.data && list.data.length === 0 ? (
        q || type ? (
          <EmptyState icon={<Search className="h-6 w-6" />} title="No experiences match" description="Try another search or kind." />
        ) : (
          <EmptyState
            illustration={<visuals.notebook className="mb-4 h-32 w-auto" />}
            title="Your journal is waiting"
            description="Record a career move, a mistake you learned from, or advice you once gave. These stories are what make your mentor genuinely personal."
            action={
              <Button onClick={() => setFormOpen(true)} icon={<NotebookPen className="h-4 w-4" />}>
                Record your first experience
              </Button>
            }
          />
        )
      ) : (
        <>
          <p className="mb-3 text-sm text-muted" aria-live="polite">
            {pluralize(list.data?.length ?? 0, "experience")}
          </p>
          <div className="space-y-4">
            <AnimatePresence>
              {list.data?.map((exp) => (
                <ExperienceCard
                  key={exp.id}
                  exp={exp}
                  typeLabel={experienceTypeLabel(exp.experience_type, types)}
                  onEdit={() => {
                    setEditing(exp);
                    setFormOpen(true);
                  }}
                  onDelete={() => setDeleting(exp)}
                />
              ))}
            </AnimatePresence>
          </div>
        </>
      )}

      <ExperienceForm
        open={formOpen}
        editing={editing}
        onClose={() => {
          setFormOpen(false);
          setEditing(null);
        }}
        onSaved={onSaved}
      />
      <ConfirmDialog
        open={!!deleting}
        title="Delete this experience?"
        message={
          <>
            <strong>{deleting?.title}</strong> will be removed from your episodic memory and your mentor will no longer recall it.
          </>
        }
        onConfirm={confirmDelete}
        onClose={() => setDeleting(null)}
        loading={busy}
      />
    </div>
  );
}
