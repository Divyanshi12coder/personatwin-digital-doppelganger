import { BarChart3, ShieldCheck, ThumbsDown, ThumbsUp } from "lucide-react";
import { useState, type ReactNode } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, LoadingState, PageHeader } from "@/components/ui/Feedback";
import { useAsync, useDocumentTitle } from "@/hooks/useAsync";
import { insightsApi } from "@/services/endpoints";
import { cn, formatDate, humanize } from "@/utils/format";

const C = { brown: "#4A2C1A", mustard: "#D4A017", gold: "#E7B84B", chocolate: "#6B4226", muted: "#806B5A", line: "#E6D9BF" };
const tooltipStyle = { borderRadius: 12, borderColor: C.line, fontSize: 12 };
const axisTick = { fill: C.muted, fontSize: 11 };

function ChartCard({ title, subtitle, empty, children, className }: { title: string; subtitle?: string; empty: boolean; children: ReactNode; className?: string }) {
  return (
    <Card className={className}>
      <CardHeader title={title} subtitle={subtitle} />
      {empty ? (
        <div className="grid h-56 place-items-center rounded-xl border border-dashed border-line bg-paper/50 px-4 text-center text-sm text-muted">
          Not enough data yet — this fills in as you use PersonaTwin.
        </div>
      ) : (
        <div className="h-64">{children}</div>
      )}
    </Card>
  );
}

const shortDate = (iso: string) => formatDate(iso, { month: "short", day: "numeric" });

export default function InsightsPage() {
  useDocumentTitle("Insights");
  const [days, setDays] = useState(90);
  const { data, error, loading, reload } = useAsync(() => insightsApi.analytics(days), [days]);

  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (loading && !data) return <LoadingState label="Crunching your numbers…" />;
  if (!data) return null;

  const totalQuestions = data.conversation_trend.reduce((a, d) => a + d.questions, 0);
  const lastGrowth = data.memory_growth[data.memory_growth.length - 1];
  const totalMemories = lastGrowth ? lastGrowth.knowledge + lastGrowth.experiences + lastGrowth.conversation : 0;
  const nothingYet = data.topics.length === 0 && data.memory_growth.length === 0;
  const groundedTotal = data.grounding.grounded + data.grounding.partial + data.grounding.ungrounded;

  return (
    <div>
      <PageHeader
        eyebrow="Your mentoring, in numbers"
        title="Insights"
        description="Computed live from your own conversations and memories — nothing here is sample data."
        actions={
          <div className="inline-flex rounded-xl border border-line bg-white p-1" role="group" aria-label="Time window">
            {[30, 90, 180].map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setDays(d)}
                aria-pressed={days === d}
                className={cn("rounded-lg px-3 py-1.5 text-sm font-medium", days === d ? "bg-brown text-cream" : "text-chocolate hover:bg-paper")}
              >
                {d}d
              </button>
            ))}
          </div>
        }
      />

      {nothingYet ? (
        <EmptyState
          icon={<BarChart3 className="h-6 w-6" />}
          title="No insights yet"
          description="Add a few memories and ask your mentor some questions. Topics, trends and memory growth will appear here."
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <ChartCard title="Conversation trend" subtitle={`${totalQuestions} questions in the last ${days} days`} empty={totalQuestions === 0} className="lg:col-span-2">
            <ResponsiveContainer>
              <AreaChart data={data.conversation_trend} margin={{ left: -20, right: 8, top: 8 }}>
                <defs>
                  <linearGradient id="q" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0" stopColor={C.mustard} stopOpacity={0.5} />
                    <stop offset="1" stopColor={C.mustard} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke={C.line} strokeDasharray="3 4" vertical={false} />
                <XAxis dataKey="date" tickFormatter={shortDate} tick={axisTick} minTickGap={28} />
                <YAxis allowDecimals={false} tick={axisTick} />
                <Tooltip contentStyle={tooltipStyle} labelFormatter={(l) => formatDate(String(l))} />
                <Area type="monotone" dataKey="questions" name="Questions" stroke={C.mustard} fill="url(#q)" strokeWidth={2} />
                <Area type="monotone" dataKey="replies" name="Mentor replies" stroke={C.brown} fill="transparent" strokeWidth={1.5} strokeDasharray="4 3" />
                <Legend wrapperStyle={{ fontSize: 12 }} />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Frequently discussed topics" subtitle="Across all your questions" empty={data.topics.length === 0}>
            <ResponsiveContainer>
              <BarChart data={data.topics} layout="vertical" margin={{ left: 24, right: 16 }}>
                <CartesianGrid stroke={C.line} strokeDasharray="3 4" horizontal={false} />
                <XAxis type="number" allowDecimals={false} tick={axisTick} />
                <YAxis type="category" dataKey="label" tick={axisTick} width={120} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#F8E8B055" }} />
                <Bar dataKey="count" name="Questions" fill={C.chocolate} radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Mentoring sessions" subtitle="Conversations started per week" empty={data.sessions_by_week.length === 0}>
            <ResponsiveContainer>
              <BarChart data={data.sessions_by_week} margin={{ left: -20, right: 8, top: 8 }}>
                <CartesianGrid stroke={C.line} strokeDasharray="3 4" vertical={false} />
                <XAxis dataKey="week" tickFormatter={shortDate} tick={axisTick} />
                <YAxis allowDecimals={false} tick={axisTick} />
                <Tooltip contentStyle={tooltipStyle} labelFormatter={(l) => `Week of ${formatDate(String(l))}`} cursor={{ fill: "#F8E8B055" }} />
                <Bar dataKey="sessions" name="Sessions" fill={C.mustard} radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="Memory growth"
            subtitle={totalMemories ? `${totalMemories} memories so far` : undefined}
            empty={data.memory_growth.length === 0}
            className="lg:col-span-2"
          >
            <ResponsiveContainer>
              <AreaChart data={data.memory_growth} margin={{ left: -20, right: 8, top: 8 }}>
                <CartesianGrid stroke={C.line} strokeDasharray="3 4" vertical={false} />
                <XAxis dataKey="date" tickFormatter={shortDate} tick={axisTick} minTickGap={28} />
                <YAxis allowDecimals={false} tick={axisTick} />
                <Tooltip contentStyle={tooltipStyle} labelFormatter={(l) => formatDate(String(l))} />
                <Area type="stepAfter" dataKey="knowledge" name="Knowledge" stackId="1" stroke={C.brown} fill={C.brown} fillOpacity={0.8} />
                <Area type="stepAfter" dataKey="experiences" name="Experiences" stackId="1" stroke={C.mustard} fill={C.mustard} fillOpacity={0.8} />
                <Area type="stepAfter" dataKey="conversation" name="Conversation notes" stackId="1" stroke={C.muted} fill={C.muted} fillOpacity={0.6} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Knowledge categories" empty={data.knowledge_categories.length === 0}>
            <ResponsiveContainer>
              <BarChart data={data.knowledge_categories.map((c) => ({ ...c, label: humanize(c.category) }))} margin={{ left: -20, right: 8, top: 8 }}>
                <CartesianGrid stroke={C.line} strokeDasharray="3 4" vertical={false} />
                <XAxis dataKey="label" tick={axisTick} interval={0} angle={-20} textAnchor="end" height={50} />
                <YAxis allowDecimals={false} tick={axisTick} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#F8E8B055" }} />
                <Bar dataKey="count" name="Documents" fill={C.gold} radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Experience types" empty={data.experience_types.length === 0}>
            <ResponsiveContainer>
              <BarChart data={data.experience_types.map((c) => ({ ...c, label: humanize(c.type) }))} margin={{ left: -20, right: 8, top: 8 }}>
                <CartesianGrid stroke={C.line} strokeDasharray="3 4" vertical={false} />
                <XAxis dataKey="label" tick={axisTick} interval={0} angle={-20} textAnchor="end" height={50} />
                <YAxis allowDecimals={false} tick={axisTick} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#F8E8B055" }} />
                <Bar dataKey="count" name="Experiences" fill={C.brown} radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <Card>
            <CardHeader title="Top tags" subtitle="Across knowledge, experiences and saved conversations" />
            {data.top_tags.length ? (
              <div className="flex flex-wrap gap-2">
                {data.top_tags.map((t) => {
                  const max = data.top_tags[0].count;
                  const scale = 0.85 + (t.count / max) * 0.5;
                  return (
                    <span key={t.tag} className="chip" style={{ fontSize: `${scale * 0.75}rem` }}>
                      #{t.tag} <span className="text-muted">{t.count}</span>
                    </span>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-muted">Tag your memories to see themes emerge.</p>
            )}
          </Card>

          <Card>
            <CardHeader title="Answer quality" subtitle="Your feedback and how answers were grounded" icon={<ShieldCheck className="h-5 w-5" />} />
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl bg-paper p-4">
                <ThumbsUp className="h-4 w-4 text-emerald-700" aria-hidden />
                <p className="mt-1 font-display text-2xl text-brown">{data.feedback.up}</p>
                <p className="text-xs text-muted">helpful</p>
              </div>
              <div className="rounded-xl bg-paper p-4">
                <ThumbsDown className="h-4 w-4 text-red-700" aria-hidden />
                <p className="mt-1 font-display text-2xl text-brown">{data.feedback.down}</p>
                <p className="text-xs text-muted">not helpful</p>
              </div>
            </div>
            {groundedTotal > 0 ? (
              <div className="mt-4">
                <div className="flex h-3 overflow-hidden rounded-full" role="img" aria-label={`Grounded ${data.grounding.grounded}, partial ${data.grounding.partial}, general ${data.grounding.ungrounded}`}>
                  <div style={{ width: `${(data.grounding.grounded / groundedTotal) * 100}%`, background: C.brown }} />
                  <div style={{ width: `${(data.grounding.partial / groundedTotal) * 100}%`, background: C.mustard }} />
                  <div style={{ width: `${(data.grounding.ungrounded / groundedTotal) * 100}%`, background: C.line }} />
                </div>
                <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted">
                  <span>■ <span style={{ color: C.brown }}>grounded</span> {data.grounding.grounded}</span>
                  <span>■ <span style={{ color: C.mustard }}>partial</span> {data.grounding.partial}</span>
                  <span>■ general {data.grounding.ungrounded}</span>
                </div>
              </div>
            ) : (
              <p className="mt-4 text-sm text-muted">Ask a few questions to see how often answers draw on your memories.</p>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
