import { Brain, Database, Download, KeyRound, LogOut, RefreshCw, Save, ShieldCheck, Trash2, UserRound } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge, ErrorState, LoadingState, PageHeader } from "@/components/ui/Feedback";
import { Input, Slider, Toggle } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { useAsync, useDocumentTitle } from "@/hooks/useAsync";
import { errorMessage } from "@/services/api";
import { authApi, healthApi, memoryApi, profileApi } from "@/services/endpoints";
import type { UserSettings } from "@/types/api";
import { downloadJson } from "@/utils/format";

export default function SettingsPage() {
  useDocumentTitle("Settings");
  const toast = useToast();
  const navigate = useNavigate();
  const { user, setUser, logout, acceptToken } = useAuth();
  const settings = useAsync(() => profileApi.settings(), []);
  const health = useAsync(() => healthApi.get(), []);
  const [draft, setDraft] = useState<UserSettings | null>(null);
  const [savingSettings, setSavingSettings] = useState(false);
  const [name, setName] = useState(user?.full_name ?? "");
  const [savingName, setSavingName] = useState(false);
  const [pw, setPw] = useState({ current: "", next: "" });
  const [pwError, setPwError] = useState<string | null>(null);
  const [savingPw, setSavingPw] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deletePw, setDeletePw] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    if (settings.data) setDraft(settings.data);
  }, [settings.data]);

  if (settings.error) return <ErrorState message={settings.error} onRetry={settings.reload} />;
  if (!draft) return <LoadingState label="Loading your preferences…" />;

  const dirty = JSON.stringify(draft) !== JSON.stringify(settings.data);

  const saveSettings = async () => {
    setSavingSettings(true);
    try {
      settings.setData(await profileApi.updateSettings(draft));
      toast.success("Preferences saved.");
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSavingSettings(false);
    }
  };

  const saveName = async (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return toast.error("Name can't be empty.");
    setSavingName(true);
    try {
      setUser(await authApi.updateMe(name.trim()));
      toast.success("Name updated.");
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSavingName(false);
    }
  };

  const changePassword = async (e: FormEvent) => {
    e.preventDefault();
    setPwError(null);
    if (pw.next.length < 8 || !/[A-Za-z]/.test(pw.next) || !/\d/.test(pw.next)) {
      return setPwError("New password needs 8+ characters with a letter and a number.");
    }
    setSavingPw(true);
    try {
      acceptToken(await authApi.changePassword(pw.current, pw.next));
      setPw({ current: "", next: "" });
      toast.success("Password changed. Other devices have been signed out.");
    } catch (err) {
      setPwError(errorMessage(err));
    } finally {
      setSavingPw(false);
    }
  };

  const reindex = async () => {
    setReindexing(true);
    try {
      const r = await memoryApi.reindex();
      toast.success(`Re-indexed ${r.knowledge_documents} documents, ${r.experiences} experiences and ${r.conversation_memories} notes.`);
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setReindexing(false);
    }
  };

  const exportData = async () => {
    setExporting(true);
    try {
      downloadJson(`personatwin-export-${new Date().toISOString().slice(0, 10)}.json`, await authApi.exportData());
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setExporting(false);
    }
  };

  const deleteAccount = async () => {
    setDeleting(true);
    setDeleteError(null);
    try {
      await authApi.deleteAccount(deletePw);
      await logout().catch(() => undefined);
      toast.info("Your account and all of its memories have been deleted.");
      navigate("/", { replace: true });
    } catch (err) {
      setDeleteError(errorMessage(err));
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="Your controls"
        title="Settings"
        description="Profile, AI behaviour, memory and privacy — all in your hands."
        actions={
          <Button
            variant="secondary"
            onClick={async () => {
              await logout();
              navigate("/login");
            }}
            icon={<LogOut className="h-4 w-4" />}
          >
            Sign out everywhere
          </Button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Profile" subtitle="How you appear in PersonaTwin" icon={<UserRound className="h-5 w-5" />} />
          <form onSubmit={saveName} className="space-y-4">
            <Input label="Full name" value={name} onChange={(e) => setName(e.target.value)} maxLength={120} required />
            <Input label="Email" value={user?.email ?? ""} disabled hint="Email can't be changed." />
            <div className="flex justify-end">
              <Button type="submit" loading={savingName} icon={<Save className="h-4 w-4" />}>
                Save name
              </Button>
            </div>
          </form>
        </Card>

        <Card>
          <CardHeader title="AI configuration" subtitle="Provider is set on the server; behaviour is yours" icon={<Brain className="h-5 w-5" />} />
          {health.data && (
            <dl className="mb-5 grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-xl bg-paper p-3">
                <dt className="text-xs text-muted">Language model</dt>
                <dd className="mt-0.5 font-medium text-brown">
                  {health.data.ai.mode === "live" ? health.data.ai.model : "Demo composer"}{" "}
                  <Badge tone={health.data.ai.mode === "live" ? "green" : "gold"}>{health.data.ai.mode}</Badge>
                </dd>
              </div>
              <div className="rounded-xl bg-paper p-3">
                <dt className="text-xs text-muted">Embeddings</dt>
                <dd className="mt-0.5 truncate font-medium text-brown">{health.data.embeddings}</dd>
              </div>
            </dl>
          )}
          <div className="space-y-6">
            <Slider
              label="Creativity"
              low="Conventional"
              high="Imaginative"
              min={0}
              max={1}
              step={0.05}
              value={draft.creativity}
              onChange={(creativity) => setDraft({ ...draft, creativity })}
              format={(v) => `${Math.round(v * 100)}%`}
            />
            <Slider
              label="Memories retrieved per question"
              low="Focused (1)"
              high="Broad (12)"
              min={1}
              max={12}
              value={draft.retrieval_top_k}
              onChange={(retrieval_top_k) => setDraft({ ...draft, retrieval_top_k })}
            />
            <Slider
              label="Minimum relevance"
              low="Inclusive"
              high="Strict"
              min={0}
              max={0.6}
              step={0.02}
              value={draft.min_relevance}
              onChange={(min_relevance) => setDraft({ ...draft, min_relevance })}
              format={(v) => v.toFixed(2)}
            />
            <Toggle
              label="Show sources in chat"
              description="Display which memories each answer used, with relevance scores."
              checked={draft.show_sources}
              onChange={(show_sources) => setDraft({ ...draft, show_sources })}
            />
          </div>
        </Card>

        <Card>
          <CardHeader title="Memory preferences" subtitle="Decide what your mentor keeps" icon={<Database className="h-5 w-5" />} />
          <div className="divide-y divide-line">
            <Toggle
              label="Save conversation history"
              description="When off, chats aren't stored at all — short-term memory lives only in your browser tab."
              checked={draft.save_conversations}
              onChange={(save_conversations) => setDraft({ ...draft, save_conversations })}
            />
            <Toggle
              label="Use saved conversation memories"
              description="Let the mentor retrieve exchanges you chose to remember (always labelled as AI-assisted)."
              checked={draft.use_conversation_memory}
              onChange={(use_conversation_memory) => setDraft({ ...draft, use_conversation_memory })}
            />
            <Toggle
              label="Automatically remember exchanges"
              description="Save every answered question as a conversation memory, instead of only the ones you pick."
              checked={draft.auto_remember}
              onChange={(auto_remember) => setDraft({ ...draft, auto_remember })}
            />
          </div>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-paper p-3">
            <p className="text-xs text-muted">Switched embedding provider? Re-embed every memory.</p>
            <Button size="sm" variant="secondary" onClick={() => void reindex()} loading={reindexing} icon={<RefreshCw className="h-3.5 w-3.5" />}>
              Re-index memories
            </Button>
          </div>
        </Card>

        <Card>
          <CardHeader title="Privacy" subtitle="Your data, your call" icon={<ShieldCheck className="h-5 w-5" />} />
          <ul className="space-y-2 text-sm text-ink/80">
            <li>• Every memory is scoped to your account — no other user can retrieve it.</li>
            <li>• AI provider keys live only on the server; your browser never contacts an AI provider.</li>
            <li>• Memories you delete are removed immediately from retrieval.</li>
          </ul>
          <Button className="mt-5" variant="secondary" onClick={() => void exportData()} loading={exporting} icon={<Download className="h-4 w-4" />}>
            Export all my data (JSON)
          </Button>
        </Card>

        <Card>
          <CardHeader title="Change password" subtitle="Signs out your other sessions" icon={<KeyRound className="h-5 w-5" />} />
          <form onSubmit={changePassword} className="space-y-4">
            {pwError && (
              <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
                {pwError}
              </p>
            )}
            <Input label="Current password" type="password" autoComplete="current-password" value={pw.current} onChange={(e) => setPw({ ...pw, current: e.target.value })} required />
            <Input label="New password" type="password" autoComplete="new-password" value={pw.next} onChange={(e) => setPw({ ...pw, next: e.target.value })} required />
            <div className="flex justify-end">
              <Button type="submit" loading={savingPw} disabled={!pw.current || !pw.next}>
                Update password
              </Button>
            </div>
          </form>
        </Card>

        <Card className="border-red-200">
          <CardHeader title="Delete account" subtitle="Permanently remove your account and every memory" icon={<Trash2 className="h-5 w-5" />} />
          <p className="text-sm text-muted">This deletes your profile, knowledge, experiences, conversations and settings. It cannot be undone.</p>
          <Button className="mt-5" variant="danger" onClick={() => setDeleteOpen(true)} icon={<Trash2 className="h-4 w-4" />}>
            Delete my account
          </Button>
        </Card>
      </div>

      {dirty && (
        <div className="sticky bottom-4 z-30 mt-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-gold bg-white px-4 py-3 shadow-lift">
          <p className="text-sm text-brown">You have unsaved AI & memory preferences.</p>
          <div className="flex gap-2">
            <Button variant="ghost" onClick={() => setDraft(settings.data)}>
              Discard
            </Button>
            <Button onClick={() => void saveSettings()} loading={savingSettings} icon={<Save className="h-4 w-4" />}>
              Save preferences
            </Button>
          </div>
        </div>
      )}

      <Modal
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        title="Delete your account?"
        description="Enter your password to confirm. This is permanent."
        footer={
          <>
            <Button variant="secondary" onClick={() => setDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={() => void deleteAccount()} loading={deleting} disabled={!deletePw}>
              Delete everything
            </Button>
          </>
        }
      >
        {deleteError && (
          <p role="alert" className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
            {deleteError}
          </p>
        )}
        <Input label="Password" type="password" autoComplete="current-password" value={deletePw} onChange={(e) => setDeletePw(e.target.value)} />
      </Modal>
    </div>
  );
}
