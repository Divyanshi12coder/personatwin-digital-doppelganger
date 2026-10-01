import { AnimatePresence } from "framer-motion";
import { Info, Save, Search, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ExperienceForm } from "@/components/memory/ExperienceForm";
import { KnowledgeForm } from "@/components/memory/KnowledgeForm";
import { MEMORY_META, MemoryCard } from "@/components/memory/MemoryCard";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState, PageHeader, Skeleton } from "@/components/ui/Feedback";
import { Input, Textarea } from "@/components/ui/Field";
import { ConfirmDialog, Modal } from "@/components/ui/Modal";
import { TagInput } from "@/components/ui/TagInput";
import { useToast } from "@/context/ToastContext";
import { useAsync, useDebounce, useDocumentTitle } from "@/hooks/useAsync";
import { errorMessage } from "@/services/api";
import { experienceApi, knowledgeApi, memoryApi } from "@/services/endpoints";
import type { ConversationMemory, Experience, KnowledgeItem, MemoryItem, MemoryType } from "@/types/api";
import { cn } from "@/utils/format";

const TABS: { key: MemoryType | ""; label: string }[] = [
  { key: "", label: "All" },
  { key: "knowledge", label: "Knowledge" },
  { key: "experience", label: "Experiences" },
  { key: "preference", label: "Preferences" },
  { key: "conversation", label: "Conversation memories" },
];

function ConversationMemoryForm({
  memory,
  onClose,
  onSaved,
}: {
  memory: ConversationMemory | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const toast = useToast();
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setTitle(memory?.title ?? "");
    setContent(memory?.content ?? "");
    setTags(memory?.tags ?? []);
  }, [memory]);

  const save = async () => {
    if (!memory) return;
    if (!title.trim() || !content.trim()) return toast.error("Title and content are required.");
    setSaving(true);
    try {
      await memoryApi.updateConversation(memory.id, { title, content, tags });
      toast.success("Conversation memory updated.");
      onSaved();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      open={!!memory}
      onClose={onClose}
      title="Edit conversation memory"
      description="Saved from a mentor conversation. It is labelled as AI-assisted and never treated as a lived experience."
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={() => void save()} loading={saving} icon={<Save className="h-4 w-4" />}>
            Save
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Input label="Title" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={200} required />
        <Textarea label="Content" rows={7} value={content} onChange={(e) => setContent(e.target.value)} maxLength={5000} required />
        <TagInput label="Tags" value={tags} onChange={setTags} lowercase />
      </div>
    </Modal>
  );
}

export default function MemoryInspectorPage() {
  useDocumentTitle("Memory Inspector");
  const toast = useToast();
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [type, setType] = useState<MemoryType | "">("");
  const debouncedQ = useDebounce(q.trim(), 350);
  const list = useAsync(() => memoryApi.list({ q: debouncedQ, type }), [debouncedQ, type]);

  const [editKnowledge, setEditKnowledge] = useState<KnowledgeItem | null>(null);
  const [editExperience, setEditExperience] = useState<Experience | null>(null);
  const [editConversation, setEditConversation] = useState<ConversationMemory | null>(null);
  const [deleting, setDeleting] = useState<MemoryItem | null>(null);
  const [busy, setBusy] = useState(false);

  const openEditor = async (item: MemoryItem) => {
    try {
      if (item.type === "preference") return navigate("/app/personality");
      if (item.ref_id === null) return;
      if (item.type === "knowledge") setEditKnowledge(await knowledgeApi.get(item.ref_id));
      if (item.type === "experience") setEditExperience(await experienceApi.get(item.ref_id));
      if (item.type === "conversation") setEditConversation(await memoryApi.getConversation(item.ref_id));
    } catch (err) {
      toast.error(errorMessage(err));
    }
  };

  const confirmDelete = async () => {
    if (!deleting || deleting.ref_id === null) return;
    setBusy(true);
    try {
      if (deleting.type === "knowledge") await knowledgeApi.remove(deleting.ref_id);
      if (deleting.type === "experience") await experienceApi.remove(deleting.ref_id);
      if (deleting.type === "conversation") await memoryApi.removeConversation(deleting.ref_id);
      toast.success("Memory deleted. Your mentor will no longer retrieve it.");
      setDeleting(null);
      void list.reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const afterSave = () => {
    setEditKnowledge(null);
    setEditExperience(null);
    setEditConversation(null);
    void list.reload();
  };

  const counts = list.data?.counts;
  const searching = Boolean(debouncedQ);

  return (
    <div>
      <PageHeader
        eyebrow="Transparency & control"
        title="Memory Inspector"
        description="Everything your mentor can remember, in one place. Search it the way your mentor does, then edit or delete anything."
      />

      <div className="card-paper mb-6 p-4 sm:p-5">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-[38px] h-4 w-4 text-muted" aria-hidden />
          <Input
            label="Test what your mentor would recall"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="e.g. should I change careers?"
            className="pl-9"
            hint="Uses the same semantic retrieval as the chat, scoped to your account, and shows relevance scores."
          />
        </div>
        <div className="mt-4 flex flex-wrap gap-2" role="tablist" aria-label="Memory type">
          {TABS.map((t) => {
            const count = t.key ? counts?.[t.key] : counts ? Object.values(counts).reduce((a, b) => a + b, 0) : undefined;
            return (
              <button
                key={t.key || "all"}
                type="button"
                role="tab"
                aria-selected={type === t.key}
                onClick={() => setType(t.key)}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                  type === t.key ? "border-brown bg-brown text-cream" : "border-line bg-white text-chocolate hover:border-chocolate/40",
                )}
              >
                {t.label}
                {count !== undefined && <span className="tabular-nums opacity-75">{count}</span>}
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_300px]">
        <div>
          {list.error ? (
            <ErrorState message={list.error} onRetry={list.reload} />
          ) : list.loading && !list.data ? (
            <div className="space-y-3">
              {[0, 1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-28" />
              ))}
            </div>
          ) : list.data && list.data.items.length === 0 ? (
            <EmptyState
              icon={<Sparkles className="h-6 w-6" />}
              title={searching ? "Nothing relevant remembered" : "No memories here yet"}
              description={
                searching
                  ? "Your mentor would answer this with general guidance and say it has no notes on it."
                  : "Add knowledge or record experiences and they'll appear here."
              }
            />
          ) : (
            <>
              {searching && (
                <p className="mb-3 text-sm text-muted" aria-live="polite">
                  Ranked by relevance to “{debouncedQ}”
                </p>
              )}
              <ul className="space-y-3">
                <AnimatePresence>
                  {list.data?.items.map((item, i) => (
                    <MemoryCard
                      key={item.id}
                      item={item}
                      index={i}
                      onEdit={() => void openEditor(item)}
                      onDelete={item.type === "preference" ? undefined : () => setDeleting(item)}
                    />
                  ))}
                </AnimatePresence>
              </ul>
            </>
          )}
        </div>

        <aside className="space-y-3 xl:sticky xl:top-8 xl:self-start">
          <div className="card-paper p-5">
            <p className="flex items-center gap-2 font-display text-lg font-semibold text-brown">
              <Info className="h-4 w-4 text-mustard-dark" aria-hidden /> How memory works
            </p>
            <ul className="mt-3 space-y-3">
              {(Object.keys(MEMORY_META) as MemoryType[]).map((k) => {
                const m = MEMORY_META[k];
                return (
                  <li key={k} className="flex gap-3">
                    <m.icon className="mt-0.5 h-4 w-4 shrink-0 text-chocolate" aria-hidden />
                    <div>
                      <p className="text-sm font-semibold text-brown">{m.label}</p>
                      <p className="text-xs text-muted">{m.kind} memory</p>
                    </div>
                  </li>
                );
              })}
            </ul>
            <p className="mt-4 text-xs text-muted">
              Short-term memory is the current conversation. Only <strong>experiences</strong> may be spoken of as personal
              memories; conversation memories are always labelled as AI-assisted.
            </p>
          </div>
        </aside>
      </div>

      <KnowledgeForm open={!!editKnowledge} editing={editKnowledge} onClose={() => setEditKnowledge(null)} onSaved={afterSave} />
      <ExperienceForm open={!!editExperience} editing={editExperience} onClose={() => setEditExperience(null)} onSaved={afterSave} />
      <ConversationMemoryForm memory={editConversation} onClose={() => setEditConversation(null)} onSaved={afterSave} />
      <ConfirmDialog
        open={!!deleting}
        title="Delete this memory?"
        message={
          <>
            <strong>{deleting?.title}</strong> will be permanently removed and will no longer be retrieved by your mentor.
          </>
        }
        onConfirm={confirmDelete}
        onClose={() => setDeleting(null)}
        loading={busy}
      />
    </div>
  );
}
