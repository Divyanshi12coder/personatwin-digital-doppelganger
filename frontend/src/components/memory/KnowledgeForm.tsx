import { FileUp, Globe, NotebookText, Save } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Input, Select, Textarea } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { TagInput } from "@/components/ui/TagInput";
import { useOptions } from "@/context/OptionsContext";
import { errorMessage } from "@/services/api";
import { knowledgeApi } from "@/services/endpoints";
import type { KnowledgeItem } from "@/types/api";
import { cn } from "@/utils/format";

type Mode = "write" | "upload" | "url";

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: (item: KnowledgeItem, created: boolean) => void;
  editing?: KnowledgeItem | null;
}

export function KnowledgeForm({ open, onClose, onSaved, editing }: Props) {
  const { options } = useOptions();
  const [mode, setMode] = useState<Mode>("write");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("general");
  const [tags, setTags] = useState<string[]>([]);
  const [isNote, setIsNote] = useState(false);
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    setError(null);
    setMode("write");
    setTitle(editing?.title ?? "");
    setContent(editing?.content ?? "");
    setCategory(editing?.category ?? "general");
    setTags(editing?.tags ?? []);
    setIsNote(editing?.source_type === "note");
    setUrl("");
    setFile(null);
  }, [open, editing]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      if (editing) {
        const item = await knowledgeApi.update(editing.id, { title, content, category, tags });
        onSaved(item, false);
      } else if (mode === "write") {
        if (!title.trim() || !content.trim()) throw new Error("Add a title and some content.");
        const item = await knowledgeApi.create({ title, content, category, tags, source_type: isNote ? "note" : "text" });
        onSaved(item, true);
      } else if (mode === "upload") {
        if (!file) throw new Error("Choose a .txt, .md or .pdf file.");
        if (file.size > 2 * 1024 * 1024) throw new Error("Files must be 2 MB or smaller.");
        const item = await knowledgeApi.upload(file, { title: title.trim() || undefined, category, tags });
        onSaved(item, true);
      } else {
        if (!/^https?:\/\//i.test(url.trim())) throw new Error("Enter a full http(s) URL.");
        const item = await knowledgeApi.importUrl({ url: url.trim(), title: title.trim() || undefined, category, tags });
        onSaved(item, true);
      }
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const tabs: { key: Mode; label: string; icon: typeof NotebookText }[] = [
    { key: "write", label: "Write", icon: NotebookText },
    { key: "upload", label: "Upload", icon: FileUp },
    { key: "url", label: "From URL", icon: Globe },
  ];

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="lg"
      title={editing ? "Edit knowledge" : "Add knowledge"}
      description={
        editing
          ? "Changes to the content are re-chunked and re-embedded automatically."
          : "Everything you add is chunked and embedded so your mentor can retrieve it."
      }
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" form="knowledge-form" loading={saving} icon={<Save className="h-4 w-4" />}>
            {editing ? "Save changes" : mode === "url" ? "Import page" : mode === "upload" ? "Upload" : "Save to vault"}
          </Button>
        </>
      }
    >
      <form id="knowledge-form" onSubmit={submit} className="space-y-5" noValidate>
        {!editing && (
          <div role="tablist" aria-label="How to add knowledge" className="inline-flex rounded-xl border border-line bg-paper p-1">
            {tabs.map((t) => (
              <button
                key={t.key}
                type="button"
                role="tab"
                aria-selected={mode === t.key}
                onClick={() => setMode(t.key)}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium",
                  mode === t.key ? "bg-white text-brown shadow-paper" : "text-muted hover:text-brown",
                )}
              >
                <t.icon className="h-4 w-4" aria-hidden /> {t.label}
              </button>
            ))}
          </div>
        )}

        {error && (
          <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-[1fr_200px]">
          <Input
            label={mode === "write" || editing ? "Title" : "Title (optional)"}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={200}
            required={mode === "write" || !!editing}
          />
          <Select label="Category" value={category} onChange={(e) => setCategory(e.target.value)}>
            {(options?.knowledge_categories ?? [{ value: "general", description: "General" }]).map((c) => (
              <option key={c.value} value={c.value}>
                {c.description}
              </option>
            ))}
          </Select>
        </div>

        {(mode === "write" || editing) && (
          <>
            <Textarea
              label="Content"
              rows={10}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Write what you know: frameworks, lessons, notes from books, explanations you give often…"
              required
            />
            {!editing && (
              <label className="flex items-center gap-2 text-sm text-chocolate">
                <input type="checkbox" checked={isNote} onChange={(e) => setIsNote(e.target.checked)} className="h-4 w-4 accent-[#6B4226]" />
                This is a quick note (not a longer piece of writing)
              </label>
            )}
          </>
        )}

        {mode === "upload" && !editing && (
          <div>
            <p className="mb-1.5 text-sm font-medium text-brown">File</p>
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              className="flex w-full flex-col items-center gap-2 rounded-xl border-2 border-dashed border-line bg-paper/60 px-4 py-8 text-sm text-muted hover:border-mustard"
            >
              <FileUp className="h-6 w-6 text-chocolate" aria-hidden />
              {file ? <span className="font-medium text-brown">{file.name}</span> : <span>Choose a .txt, .md or .pdf file (max 2 MB)</span>}
            </button>
            <input
              ref={fileRef}
              type="file"
              accept=".txt,.md,.markdown,.pdf,text/plain,text/markdown,application/pdf"
              className="sr-only"
              aria-label="Choose file"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
        )}

        {mode === "url" && !editing && (
          <Input
            label="Page URL"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/an-article-you-wrote"
            hint="Public pages only. The readable text is extracted on the server."
            required
          />
        )}

        <TagInput label="Tags" value={tags} onChange={setTags} lowercase placeholder="e.g. habits" />
      </form>
    </Modal>
  );
}
