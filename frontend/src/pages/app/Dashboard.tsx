import {
  Activity,
  AlertCircle,
  ArrowRight,
  BookOpen,
  Brain,
  CheckCircle2,
  Circle,
  MessageCircle,
  NotebookPen,
  Sparkles,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { MentorProfileCard } from "@/components/memory/MentorProfileCard";
import { ButtonLink } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge, ErrorState, LoadingState, PageHeader, StatCard } from "@/components/ui/Feedback";
import { useAuth } from "@/context/AuthContext";
import { useAsync, useDocumentTitle } from "@/hooks/useAsync";
import { insightsApi } from "@/services/endpoints";
import { pluralize, relativeTime, topicLabel } from "@/utils/format";

const PIE_COLORS = ["#4A2C1A", "#D4A017", "#806B5A"];

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
}

export default function DashboardPage() {
  useDocumentTitle("Dashboard");
  const { user } = useAuth();
  const { data, error, loading, reload } = useAsync(() => insightsApi.overview(), []);

  if (loading && !data) return <LoadingState label="Gathering your notes…" />;
  if (error || !data) return <ErrorState message={error ?? "No data"} onRetry={reload} />;

  const { counts, memory_health: health } = data;
  const composition = [
    { name: "Knowledge", value: counts.knowledge_documents },
    { name: "Experiences", value: counts.experiences },
    { name: "Conversation notes", value: counts.conversation_memories },
  ];
  const hasMemories = counts.total_memories > 0;
  const quickstart = [
    { done: data.profile.completeness >= 70, label: "Describe your mentoring philosophy", to: "/app/personality" },
    { done: counts.knowledge_documents > 0, label: "Add your first knowledge note", to: "/app/knowledge" },
    { done: counts.experiences >= 3, label: "Record three experiences", to: "/app/experiences" },
    { done: counts.questions_asked > 0, label: "Ask your mentor a question", to: "/app/chat" },
  ];
  const healthTone = health.status === "healthy" ? "green" : health.status === "empty" ? "default" : "gold";

  return (
    <div>
      <PageHeader
        eyebrow={new Intl.DateTimeFormat(undefined, { weekday: "long", month: "long", day: "numeric" }).format(new Date())}
        title={`${greeting()}, ${user?.full_name.split(" ")[0] ?? "there"}`}
        description="Here's what your twin knows, remembers and has been talking about."
        actions={
          <>
            <ButtonLink to="/app/experiences" variant="secondary" icon={<NotebookPen className="h-4 w-4" />}>
              Record an experience
            </ButtonLink>
            <ButtonLink to="/app/chat" icon={<MessageCircle className="h-4 w-4" />}>
              Ask your mentor
            </ButtonLink>
          </>
        }
      />

      {data.ai.mode === "demo" && (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-gold/60 bg-softgold/40 px-4 py-3 text-sm text-brown">
          <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-mustard-dark" aria-hidden />
          <p>
            <strong>Demo mode:</strong> no AI provider key is configured on the server, so replies are composed directly
            from your retrieved memories. Set <code className="rounded bg-white/70 px-1">AI_PROVIDER</code> and{" "}
            <code className="rounded bg-white/70 px-1">AI_API_KEY</code> on the backend to enable full LLM reasoning.
          </p>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Memories" value={counts.total_memories} hint="knowledge + experiences + notes" icon={<Brain className="h-5 w-5" />} />
        <StatCard
          label="Knowledge"
          value={counts.knowledge_documents}
          hint={`${pluralize(counts.knowledge_chunks, "indexed chunk")}`}
          icon={<BookOpen className="h-5 w-5" />}
          delay={0.05}
        />
        <StatCard
          label="Experiences"
          value={counts.experiences}
          hint={`${health.experiences_with_lessons} with lessons`}
          icon={<NotebookPen className="h-5 w-5" />}
          delay={0.1}
        />
        <StatCard
          label="Conversations"
          value={counts.conversations}
          hint={pluralize(counts.questions_asked, "question") + " asked"}
          icon={<MessageCircle className="h-5 w-5" />}
          delay={0.15}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.15fr_1fr]">
        <MentorProfileCard profile={data.profile} />

        <Card>
          <CardHeader
            title="Memory health"
            subtitle="How ready your twin is to give grounded answers"
            icon={<Activity className="h-5 w-5" />}
            action={<Badge tone={healthTone}>{health.status.replace("_", " ")}</Badge>}
          />
          <div>
            <div className="mb-1 flex justify-between text-xs text-muted">
              <span>Indexed for semantic search</span>
              <span>{Math.round(health.indexed_ratio * 100)}%</span>
            </div>
            <div className="h-2 rounded-full bg-line">
              <div className="h-2 rounded-full bg-mustard transition-all" style={{ width: `${health.indexed_ratio * 100}%` }} />
            </div>
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-xl bg-paper p-3">
              <dt className="text-xs text-muted">Knowledge categories</dt>
              <dd className="font-display text-xl text-brown">{health.categories_covered}</dd>
            </div>
            <div className="rounded-xl bg-paper p-3">
              <dt className="text-xs text-muted">Unindexed items</dt>
              <dd className="font-display text-xl text-brown">{health.unindexed_items}</dd>
            </div>
          </dl>
          {health.issues.length > 0 ? (
            <ul className="mt-4 space-y-2">
              {health.issues.map((issue) => (
                <li key={issue} className="flex gap-2 text-sm text-ink/80">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-mustard-dark" aria-hidden /> {issue}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-4 flex items-center gap-2 text-sm text-emerald-800">
              <CheckCircle2 className="h-4 w-4" aria-hidden /> Everything is indexed and well described.
            </p>
          )}
        </Card>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Card>
          <CardHeader title="Memory composition" subtitle="What your twin draws from" />
          {hasMemories ? (
            <div className="flex items-center gap-4">
              <div className="h-40 w-40 shrink-0">
                <ResponsiveContainer>
                  <PieChart>
                    <Pie data={composition} dataKey="value" innerRadius={42} outerRadius={70} paddingAngle={2} stroke="none">
                      {composition.map((_, i) => (
                        <Cell key={i} fill={PIE_COLORS[i]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: 12, borderColor: "#E6D9BF" }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <ul className="space-y-2 text-sm">
                {composition.map((c, i) => (
                  <li key={c.name} className="flex items-center gap-2">
                    <span className="h-3 w-3 rounded-sm" style={{ background: PIE_COLORS[i] }} aria-hidden />
                    <span className="text-muted">{c.name}</span>
                    <span className="font-semibold text-brown">{c.value}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-sm text-muted">No memories yet — the chart fills in as you add knowledge and experiences.</p>
          )}
        </Card>

        <Card>
          <CardHeader title="Active topics" subtitle="Last 30 days of questions" />
          {data.active_topics.length ? (
            <ul className="space-y-3">
              {data.active_topics.map((t) => {
                const max = data.active_topics[0].count;
                return (
                  <li key={t.topic}>
                    <div className="mb-1 flex justify-between text-sm">
                      <span className="text-brown">{t.label}</span>
                      <span className="text-muted">{t.count}</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-line">
                      <div className="h-1.5 rounded-full bg-chocolate" style={{ width: `${(t.count / max) * 100}%` }} />
                    </div>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="text-sm text-muted">Topics appear once you start asking your mentor questions.</p>
          )}
        </Card>

        <Card>
          <CardHeader
            title="Recent conversations"
            action={
              <Link to="/app/chat" className="text-xs font-semibold text-chocolate hover:underline">
                Open chat
              </Link>
            }
          />
          {data.recent_conversations.length ? (
            <ul className="divide-y divide-line">
              {data.recent_conversations.map((c) => (
                <li key={c.id}>
                  <Link to={`/app/chat/${c.id}`} className="group flex items-center justify-between gap-3 py-2.5">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-brown group-hover:underline">{c.title}</p>
                      <p className="text-xs text-muted">
                        {topicLabel(c.topic)} · {pluralize(c.message_count, "message")} · {relativeTime(c.updated_at)}
                      </p>
                    </div>
                    <ArrowRight className="h-4 w-4 shrink-0 text-muted group-hover:text-chocolate" aria-hidden />
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted">No conversations yet.</p>
          )}
        </Card>
      </div>

      {quickstart.some((q) => !q.done) && (
        <Card className="mt-6" ruled>
          <CardHeader title="Getting started" subtitle="A few steps to a mentor that genuinely sounds like you" />
          <ul className="grid gap-2 sm:grid-cols-2">
            {quickstart.map((q) => (
              <li key={q.label}>
                <Link
                  to={q.to}
                  className="flex items-center gap-3 rounded-xl bg-white/80 px-3 py-2.5 text-sm hover:bg-softgold/40"
                >
                  {q.done ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-700" aria-label="Done" />
                  ) : (
                    <Circle className="h-5 w-5 text-muted" aria-label="Not done yet" />
                  )}
                  <span className={q.done ? "text-muted line-through" : "text-brown"}>{q.label}</span>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
