import { AnimatePresence } from "framer-motion";
import { BookOpen, Plus, Search } from "lucide-react";
import { useState } from "react";
import { KnowledgeCard } from "@/components/memory/KnowledgeCard";
import { KnowledgeForm } from "@/components/memory/KnowledgeForm";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState, PageHeader, Skeleton } from "@/components/ui/Feedback";
import { Input, Select } from "@/components/ui/Field";
import { ConfirmDialog } from "@/components/ui/Modal";
import { visuals } from "@/config/visuals";
import { useOptions } from "@/context/OptionsContext";
import { useToast } from "@/context/ToastContext";
import { useAsync, useDebounce, useDocumentTitle } from "@/hooks/useAsync";
import { errorMessage } from "@/services/api";
import { knowledgeApi, memoryApi } from "@/services/endpoints";
import type { KnowledgeItem } from "@/types/api";
import { pluralize } from "@/utils/format";

export default function KnowledgePage() {
  useDocumentTitle("Knowledge Vault");
  const toast = useToast();
  const { options } = useOptions();
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [tag, setTag] = useState("");
  const debouncedQ = useDebounce(q, 300);
  const list = useAsync(() => knowledgeApi.list({ q: debouncedQ, category, tag }), [debouncedQ, category, tag]);
  const tags = useAsync(() => memoryApi.tags(), []);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<KnowledgeItem | null>(null);
  const [deleting, setDeleting] = useState<KnowledgeItem | null>(null);
  const [busy, setBusy] = useState(false);

  const filtersActive = Boolean(q || category || tag);

  const onSaved = (item: KnowledgeItem, created: boolean) => {
    setFormOpen(false);
    setEditing(null);
    toast.success(created ? `Saved "${item.title}" — ${pluralize(item.chunk_count, "chunk")} indexed.` : "Changes saved and re-indexed.");
    void list.reload();
    void tags.reload();
  };

  const confirmDelete = async () => {
    if (!deleting) return;
    setBusy(true);
    try {
      await knowledgeApi.remove(deleting.id);
      list.setData((prev) => (prev ? { items: prev.items.filter((i) => i.id !== deleting.id), total: prev.total - 1 } : prev));
      toast.success("Deleted from your Knowledge Vault.");
      setDeleting(null);
      void tags.reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="Long-term semantic memory"
        title="Knowledge Vault"
        description="Notes, documents and pages your mentor can draw on. Each item is chunked, embedded and searchable."
        actions={
          <Button
            onClick={() => {
              setEditing(null);
              setFormOpen(true);
            }}
            icon={<Plus className="h-4 w-4" />}
          >
            Add knowledge
          </Button>
        }
      />

      <div className="card-paper mb-6 grid gap-3 p-4 sm:grid-cols-[1fr_200px_180px]">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-[38px] h-4 w-4 text-muted" aria-hidden />
          <Input label="Search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search titles and content" className="pl-9" />
        </div>
        <Select label="Category" value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {options?.knowledge_categories.map((c) => (
            <option key={c.value} value={c.value}>
              {c.description}
            </option>
          ))}
        </Select>
        <Select label="Tag" value={tag} onChange={(e) => setTag(e.target.value)}>
          <option value="">All tags</option>
          {tags.data?.map((t) => (
            <option key={t.name} value={t.name}>
              #{t.name} ({t.count})
            </option>
          ))}
        </Select>
      </div>

      {list.error ? (
        <ErrorState message={list.error} onRetry={list.reload} />
      ) : list.loading && !list.data ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-56" />
          ))}
        </div>
      ) : list.data && list.data.items.length === 0 ? (
        filtersActive ? (
          <EmptyState icon={<Search className="h-6 w-6" />} title="Nothing matches" description="Try a different search, category or tag." />
        ) : (
          <EmptyState
            illustration={<visuals.openBook className="mb-4 h-28 w-auto" />}
            title="Your vault is empty"
            description="Add the things you know and explain often — frameworks, study methods, lessons from books. Your mentor retrieves them when they're relevant."
            action={
              <Button onClick={() => setFormOpen(true)} icon={<BookOpen className="h-4 w-4" />}>
                Add your first note
              </Button>
            }
          />
        )
      ) : (
        <>
          <p className="mb-3 text-sm text-muted" aria-live="polite">
            {pluralize(list.data?.total ?? 0, "item")}
          </p>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <AnimatePresence>
              {list.data?.items.map((item, i) => (
                <KnowledgeCard
                  key={item.id}
                  item={item}
                  index={i}
                  onEdit={() => {
                    setEditing(item);
                    setFormOpen(true);
                  }}
                  onDelete={() => setDeleting(item)}
                />
              ))}
            </AnimatePresence>
          </div>
        </>
      )}

      <KnowledgeForm
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
        title="Delete this knowledge?"
        message={
          <>
            <strong>{deleting?.title}</strong> and its embedded chunks will be permanently removed. Past answers that cited it
            keep their snapshot.
          </>
        }
        onConfirm={confirmDelete}
        onClose={() => setDeleting(null)}
        loading={busy}
      />
    </div>
  );
}
