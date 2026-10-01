import { motion, useReducedMotion, type Variants } from "framer-motion";
import {
  ArrowDown,
  ArrowRight,
  BookOpen,
  Brain,
  Briefcase,
  CheckCircle2,
  Compass,
  Database,
  GraduationCap,
  KeyRound,
  Lightbulb,
  Lock,
  MessageCircle,
  NotebookPen,
  Palette,
  Scale,
  ShieldCheck,
  Sparkles,
  Timer,
  Trash2,
  Users,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { StickyNote } from "@/components/illustrations/Illustrations";
import { Brand } from "@/components/layout/Brand";
import { ButtonLink } from "@/components/ui/Button";
import { visuals } from "@/config/visuals";
import { useAuth } from "@/context/AuthContext";
import { useDocumentTitle } from "@/hooks/useAsync";
import { cn } from "@/utils/format";

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 18 },
  show: (i: number = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.5, delay: i * 0.08, ease: "easeOut" } }),
};

function Section({
  id,
  eyebrow,
  title,
  intro,
  children,
  className,
}: {
  id: string;
  eyebrow: string;
  title: string;
  intro?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className={cn("scroll-mt-20 py-20 sm:py-24", className)}>
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <motion.div
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-80px" }}
          variants={fadeUp}
          className="mx-auto mb-12 max-w-2xl text-center"
        >
          <p className="label-hand mb-2">{eyebrow}</p>
          <h2 id={`${id}-title`} className="text-balance text-3xl font-semibold sm:text-4xl">
            {title}
          </h2>
          {intro && <p className="section-intro mt-4 text-base text-muted sm:text-lg">{intro}</p>}
        </motion.div>
        {children}
      </div>
    </section>
  );
}

function Navbar() {
  const { user } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  const links = [
    ["How it works", "#how-it-works"],
    ["Memory", "#memory"],
    ["Use cases", "#use-cases"],
    ["Privacy", "#privacy"],
  ];
  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-all",
        scrolled ? "border-b border-line bg-cream/90 shadow-sm backdrop-blur" : "bg-transparent",
      )}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Brand />
        <nav aria-label="Sections" className="hidden items-center gap-7 md:flex">
          {links.map(([label, href]) => (
            <a key={href} href={href} className="text-sm font-medium text-chocolate hover:text-brown">
              {label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          {user ? (
            <ButtonLink to={user.onboarding_completed ? "/app" : "/onboarding"} size="sm">
              Open my study
            </ButtonLink>
          ) : (
            <>
              <Link to="/login" className="hidden rounded-lg px-3 py-1.5 text-sm font-medium text-chocolate hover:text-brown sm:inline">
                Sign in
              </Link>
              <ButtonLink to="/signup" size="sm">
                Build your mentor
              </ButtonLink>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

/** The hero "Mentor Desk": notebook, pen, profile card, memory snippets, AI connections. */
function MentorDesk() {
  const reduce = useReducedMotion();
  const float = (delay: number) =>
    reduce ? {} : { animate: { y: [0, -6, 0] }, transition: { duration: 5, repeat: Infinity, delay, ease: "easeInOut" as const } };
  const inputs = [
    { label: "Experience", x: "4%", y: "6%", d: 0 },
    { label: "Knowledge", x: "60%", y: "1%", d: 0.6 },
    { label: "Values", x: "0%", y: "72%", d: 1.2 },
    { label: "Mentoring Style", x: "58%", y: "80%", d: 1.8 },
  ];
  const Notebook = visuals.notebook;
  const Pen = visuals.fountainPen;
  const Lamp = visuals.lamp;

  return (
    <div className="relative mx-auto aspect-[5/5] w-full max-w-[540px]" aria-hidden>
      <div className="absolute inset-[8%] rounded-full bg-softgold/60 blur-3xl" />
      <Lamp className="absolute -top-6 right-[6%] h-40 w-32 opacity-80" />

      {/* connection lines toward the twin */}
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
        {[
          [18, 12],
          [78, 8],
          [12, 78],
          [76, 86],
        ].map(([x, y], i) => (
          <motion.path
            key={i}
            d={`M${x} ${y} Q 50 56 50 56`}
            stroke="#6B4226"
            strokeOpacity="0.35"
            strokeWidth="0.35"
            strokeDasharray="1.2 1.4"
            fill="none"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.4, delay: 0.4 + i * 0.15 }}
          />
        ))}
      </svg>

      <motion.div
        initial={{ opacity: 0, rotate: -8, y: 20 }}
        animate={{ opacity: 1, rotate: -6, y: 0 }}
        transition={{ duration: 0.7 }}
        className="absolute left-[16%] top-[16%] w-[46%]"
      >
        <Notebook className="h-auto w-full drop-shadow-xl" />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, x: 40 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.7, delay: 0.3 }}
        className="absolute left-[32%] top-[68%] w-[50%] rotate-[-18deg]"
      >
        <Pen className="h-auto w-full drop-shadow-lg" />
      </motion.div>

      {/* profile card */}
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.5 }}
        className="card-paper absolute right-0 top-[13%] w-[46%] p-4"
      >
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 shrink-0 place-items-center overflow-hidden rounded-full border-2 border-gold bg-softgold">
            <visuals.mentor className="h-11 w-11" />
          </span>
          <div>
            <p className="font-display text-sm font-semibold text-brown">Your PersonaTwin</p>
            <p className="text-[11px] text-muted">warm · step-by-step · candid</p>
          </div>
        </div>
        <div className="mt-3 space-y-1.5">
          <div className="rounded-lg bg-paper px-2.5 py-1.5 text-[11px] text-chocolate">
            <span className="font-semibold">E1</span> · "Test a career change with small experiments…"
          </div>
          <div className="rounded-lg bg-paper px-2.5 py-1.5 text-[11px] text-chocolate">
            <span className="font-semibold">K2</span> · "Spaced repetition beats cramming."
          </div>
        </div>
      </motion.div>

      {/* center twin node */}
      <motion.div
        initial={{ scale: 0.6, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.9, type: "spring", stiffness: 160 }}
        className="absolute left-[50%] top-[56%] -translate-x-1/2 -translate-y-1/2"
      >
        <div className="flex items-center gap-2 rounded-full border border-gold bg-brown px-4 py-2 font-display text-sm font-semibold text-cream shadow-lift">
          <Sparkles className="h-4 w-4 text-gold" /> PersonaTwin
        </div>
      </motion.div>

      {inputs.map((n) => (
        <motion.div key={n.label} className="absolute" style={{ left: n.x, top: n.y }} {...float(n.d)}>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-white/95 px-3 py-1.5 text-xs font-semibold text-chocolate shadow-paper">
            <span className="h-2 w-2 rounded-full bg-mustard" />
            {n.label}
          </span>
        </motion.div>
      ))}

      <div className="absolute -bottom-2 left-[2%] hidden sm:block">
        <StickyNote text="Mistakes are data, not verdicts." rotate={-5} />
      </div>
    </div>
  );
}

const FLOW = [
  { icon: NotebookPen, title: "Your Experiences", text: "Structured episodes: the situation, what happened, what you learned." },
  { icon: BookOpen, title: "Your Knowledge", text: "Notes, documents and pages — chunked and embedded into pgvector." },
  { icon: Palette, title: "Your Personality", text: "Tone, teaching approach, values and philosophy you configure." },
  { icon: Database, title: "Memory Retrieval", text: "Semantic search over only your memories, filtered by owner." },
  { icon: Brain, title: "AI Reasoning", text: "An LLM reasons over labelled memories, with strict grounding rules." },
  { icon: MessageCircle, title: "Mentor Response", text: "Validated, cited answer — or an honest “I don't have notes on that.”" },
];

const MEMORY = [
  {
    icon: BookOpen,
    title: "Knowledge",
    kind: "Long-term semantic memory",
    text: "What you know. Documents are split into overlapping chunks and embedded for similarity search.",
  },
  {
    icon: NotebookPen,
    title: "Experiences",
    kind: "Episodic memory",
    text: "What you lived. Specific stories with lessons — the only source the mentor may speak of as “I remember…”.",
  },
  {
    icon: Brain,
    title: "Preferences",
    kind: "Persona memory",
    text: "How you mentor. Communication style, values and philosophy shape every answer's voice.",
  },
  {
    icon: MessageCircle,
    title: "Conversations",
    kind: "Short-term + opt-in memory",
    text: "Recent turns give context; exchanges you choose to save become clearly-labelled notes.",
  },
];

const USE_CASES = [
  { icon: Briefcase, title: "Career Mentor", text: "Weigh a job change against the lessons from your own career moves." },
  { icon: GraduationCap, title: "Study Mentor", text: "Turn your study techniques into patient, repeatable guidance." },
  { icon: Users, title: "Leadership Mentor", text: "Share how you give feedback, delegate and handle hard conversations." },
  { icon: Lightbulb, title: "Creative Mentor", text: "Pass on your process for getting unstuck and shipping creative work." },
  { icon: Timer, title: "Productivity Mentor", text: "Encode the routines and priorities that actually work for you." },
  { icon: Scale, title: "Decision Mentor", text: "Apply your decision principles to new dilemmas, step by step." },
];

export default function LandingPage() {
  useDocumentTitle("");
  const { user } = useAuth();
  const ctaTarget = user ? (user.onboarding_completed ? "/app" : "/onboarding") : "/signup";

  return (
    <div className="overflow-x-hidden">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Navbar />

      <main id="main">
        {/* HERO */}
        <section className="relative overflow-hidden pb-16 pt-28 sm:pb-24 sm:pt-32" aria-labelledby="hero-title">
          <div className="ruled-margin absolute inset-0 opacity-60" aria-hidden />
          <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-b from-transparent to-cream" aria-hidden />
          <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 sm:px-6 lg:grid-cols-[1.05fr_1fr]">
            <motion.div initial="hidden" animate="show" variants={fadeUp}>
              <p className="label-hand mb-3 text-2xl">Your digital doppelganger mentor</p>
              <h1 id="hero-title" className="text-balance text-4xl font-semibold leading-[1.08] sm:text-5xl lg:text-6xl">
                Meet the version of you that{" "}
                <span className="relative whitespace-nowrap">
                  <span className="relative z-10">never forgets</span>
                  <svg className="absolute -bottom-1 left-0 z-0 h-3 w-full" viewBox="0 0 200 12" preserveAspectRatio="none" aria-hidden>
                    <path d="M2 8c40-6 120-8 196-2" stroke="#D4A017" strokeWidth="6" strokeLinecap="round" fill="none" opacity="0.7" />
                  </svg>
                </span>{" "}
                what you've learned.
              </h1>
              <p className="mt-6 max-w-xl text-lg text-ink/75">
                PersonaTwin transforms your knowledge, experiences, and mentoring style into a personalized AI
                companion — one that answers from <em>your</em> memories, cites them, and admits when it doesn't know.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <ButtonLink to={ctaTarget} size="lg" icon={<Sparkles className="h-4 w-4" />}>
                  Build Your Mentor
                </ButtonLink>
                <a
                  href="#how-it-works"
                  className="inline-flex h-12 items-center gap-2 rounded-xl border border-line bg-white px-6 text-base font-medium text-brown hover:bg-paper"
                >
                  Explore How It Works <ArrowDown className="h-4 w-4" />
                </a>
              </div>
              <ul className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-chocolate">
                {["Grounded in your own memories", "Cited sources", "You control what it remembers"].map((t) => (
                  <li key={t} className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4 text-mustard-dark" aria-hidden /> {t}
                  </li>
                ))}
              </ul>
            </motion.div>
            <MentorDesk />
          </div>
        </section>

        {/* WHAT IS IT */}
        <Section
          id="what"
          eyebrow="What is PersonaTwin?"
          title="Not a chatbot with a personality prompt."
          intro="A real memory system — knowledge, lived experiences and mentoring style stored separately, retrieved semantically, and reasoned over by an LLM that is never allowed to invent your past."
        >
          <div className="grid gap-5 md:grid-cols-3">
            {[
              {
                v: visuals.openBook,
                title: "It knows what you know",
                text: "Add notes, documents and web pages to your Knowledge Vault. Everything is chunked, embedded and searchable.",
              },
              {
                v: visuals.notebook,
                title: "It remembers what you lived",
                text: "Record experiences as structured episodes. Your twin draws on them — and cites them — when they're relevant.",
              },
              {
                v: visuals.mentor,
                title: "It sounds like you",
                text: "Tune tone, directness, teaching approach and values. It's a communication profile you control, not a diagnosis.",
              },
            ].map((c, i) => (
              <motion.article
                key={c.title}
                custom={i}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true }}
                variants={fadeUp}
                className="card-paper p-6"
              >
                <div className="mb-5 grid h-32 place-items-center rounded-xl bg-paper">
                  <c.v className="h-24 w-auto" />
                </div>
                <h3 className="text-xl font-semibold">{c.title}</h3>
                <p className="mt-2 text-sm text-muted">{c.text}</p>
              </motion.article>
            ))}
          </div>
        </Section>

        {/* HOW IT THINKS */}
        <Section
          id="how-it-works"
          eyebrow="How it thinks"
          title="From your notebook to a grounded answer"
          intro="Every question runs the same transparent pipeline. You can watch each step in the chat."
          className="bg-paper/70"
        >
          <ol className="relative grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FLOW.map((step, i) => (
              <motion.li
                key={step.title}
                custom={i}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true }}
                variants={fadeUp}
                className="card-paper relative p-5"
              >
                <div className="flex items-center gap-3">
                  <span className="grid h-10 w-10 place-items-center rounded-xl bg-brown text-gold">
                    <step.icon className="h-5 w-5" aria-hidden />
                  </span>
                  <span className="font-hand text-2xl text-mustard-dark">0{i + 1}</span>
                </div>
                <h3 className="mt-3 text-lg font-semibold">{step.title}</h3>
                <p className="mt-1 text-sm text-muted">{step.text}</p>
                {(i + 1) % 3 !== 0 && (
                  <ArrowRight className="absolute -right-[18px] top-1/2 z-10 hidden h-5 w-5 -translate-y-1/2 text-mustard lg:block" aria-hidden />
                )}
              </motion.li>
            ))}
          </ol>
        </Section>

        {/* MEMORY ARCHITECTURE */}
        <Section
          id="memory"
          eyebrow="Memory architecture"
          title="Four kinds of memory, kept honestly apart"
          intro="Facts, lived experiences, preferences and AI-generated conversation are stored and labelled separately — so a generated answer can never masquerade as a real memory."
        >
          <div className="grid items-center gap-10 lg:grid-cols-[1fr_1.2fr]">
            <div className="card-paper dot-grid p-6">
              <visuals.chalkboard className="h-auto w-full" />
              <p className="mt-4 text-center font-hand text-xl text-chocolate">Retrieval connects a question to the right memories</p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              {MEMORY.map((m, i) => (
                <motion.div
                  key={m.title}
                  custom={i}
                  initial="hidden"
                  whileInView="show"
                  viewport={{ once: true }}
                  variants={fadeUp}
                  className="card-paper p-5"
                >
                  <span className="grid h-10 w-10 place-items-center rounded-xl bg-softgold text-chocolate">
                    <m.icon className="h-5 w-5" aria-hidden />
                  </span>
                  <h3 className="mt-3 text-lg font-semibold">{m.title}</h3>
                  <p className="text-xs font-semibold uppercase tracking-wider text-mustard-dark">{m.kind}</p>
                  <p className="mt-2 text-sm text-muted">{m.text}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </Section>

        {/* PERSONALITY */}
        <Section
          id="personality"
          eyebrow="Personality modeling"
          title="Your voice, configured — not guessed"
          intro="Choose how your twin communicates. These settings shape tone and structure; they are a persona profile, not a psychological assessment."
          className="bg-paper/70"
        >
          <div className="grid items-center gap-10 lg:grid-cols-2">
            <div className="card-paper ruled space-y-5 p-6 sm:p-8" aria-label="Example persona profile">
              <p className="label-hand">An example profile</p>
              {[
                ["Formality", "casual", "formal", 30],
                ["Directness", "gentle", "direct", 68],
                ["Warmth", "reserved", "warm", 82],
                ["Humor", "serious", "playful", 25],
              ].map(([label, lo, hi, v]) => (
                <div key={label as string}>
                  <div className="mb-1.5 flex justify-between text-sm font-medium text-brown">
                    <span>{label}</span>
                    <span className="text-xs text-muted">
                      {lo} → {hi}
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-line">
                    <motion.div
                      className="h-2 rounded-full bg-gradient-to-r from-gold to-mustard"
                      initial={{ width: 0 }}
                      whileInView={{ width: `${v}%` }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.9 }}
                    />
                  </div>
                </div>
              ))}
              <div className="flex flex-wrap gap-2 pt-2">
                {["Socratic questions", "Values-led decisions", "Celebrates progress", "Curiosity", "Honesty"].map((t) => (
                  <span key={t} className="chip">
                    {t}
                  </span>
                ))}
              </div>
            </div>
            <div className="space-y-4">
              {[
                ["Communication style", "Warm, direct, analytical, storytelling or Socratic."],
                ["Teaching approach", "Examples first, first principles, step-by-step, questions or hands-on."],
                ["Mentoring philosophy", "How you encourage, handle mistakes, face hard decisions and teach."],
                ["Boundaries", "Topics your twin should steer away from."],
              ].map(([t, d]) => (
                <div key={t} className="flex gap-4">
                  <CheckCircle2 className="mt-1 h-5 w-5 shrink-0 text-mustard-dark" aria-hidden />
                  <div>
                    <h3 className="text-lg font-semibold">{t}</h3>
                    <p className="text-sm text-muted">{d}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Section>

        {/* USE CASES */}
        <Section
          id="use-cases"
          eyebrow="Use cases"
          title="A mentor for the things you know best"
          intro="PersonaTwin passes on your perspective. It is not a substitute for licensed medical, legal, financial or mental-health advice."
        >
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {USE_CASES.map((u, i) => (
              <motion.article
                key={u.title}
                custom={i}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true }}
                variants={fadeUp}
                whileHover={{ y: -4 }}
                className="card-paper group p-6"
              >
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-brown text-gold transition-colors group-hover:bg-mustard group-hover:text-ink">
                  <u.icon className="h-5 w-5" aria-hidden />
                </span>
                <h3 className="mt-4 text-xl font-semibold">{u.title}</h3>
                <p className="mt-2 text-sm text-muted">{u.text}</p>
              </motion.article>
            ))}
          </div>
        </Section>

        {/* PRIVACY */}
        <Section
          id="privacy"
          eyebrow="Privacy"
          title="Your memories stay yours"
          intro="Every query is scoped to your account, and you decide what is remembered."
          className="bg-brown text-cream [&_.label-hand]:text-gold [&_.section-intro]:text-cream/80 [&_h2]:text-cream"
        >
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { icon: Lock, title: "Strict isolation", text: "Every database query filters by your user id — another account can never retrieve your memories." },
              { icon: ShieldCheck, title: "Memory controls", text: "Turn off conversation saving, disable conversation memory, or choose exactly which exchanges to keep." },
              { icon: Trash2, title: "Edit, export, delete", text: "Inspect every memory, edit or delete it, export all your data as JSON, or delete your account." },
              { icon: KeyRound, title: "Keys stay server-side", text: "The browser never talks to an AI provider. API keys live only in backend environment variables." },
              { icon: Compass, title: "Honest by design", text: "Responses are validated: invented citations are removed and unsupported “memories” are flagged." },
              { icon: Brain, title: "Bring your own model", text: "Use Claude or an OpenAI-compatible model — or run fully offline in demo mode." },
            ].map((p, i) => (
              <motion.div
                key={p.title}
                custom={i}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true }}
                variants={fadeUp}
                className="rounded-note border border-white/10 bg-white/5 p-6"
              >
                <p.icon className="h-6 w-6 text-gold" aria-hidden />
                <h3 className="mt-3 text-lg font-semibold text-cream">{p.title}</h3>
                <p className="mt-1.5 text-sm text-cream/75">{p.text}</p>
              </motion.div>
            ))}
          </div>
        </Section>

        {/* TECHNOLOGY */}
        <Section id="technology" eyebrow="Technology" title="Built like a real product" intro="Open, inspectable architecture from database to model.">
          <div className="grid gap-8 lg:grid-cols-[1.2fr_1fr]">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {[
                ["React + TypeScript", "Vite, Tailwind, Framer Motion"],
                ["FastAPI", "Pydantic, dependency injection"],
                ["PostgreSQL", "SQLAlchemy 2 + Alembic"],
                ["pgvector", "HNSW cosine search"],
                ["RAG pipeline", "chunk → embed → retrieve"],
                ["JWT auth", "bcrypt, token revocation"],
                ["Claude / OpenAI", "pluggable provider layer"],
                ["Docker Compose", "postgres · api · web"],
                ["pytest", "isolation & pipeline tests"],
              ].map(([t, d]) => (
                <div key={t} className="card-paper p-4">
                  <p className="font-display font-semibold text-brown">{t}</p>
                  <p className="mt-0.5 text-xs text-muted">{d}</p>
                </div>
              ))}
            </div>
            <div className="card-paper grid place-items-center p-6">
              <visuals.knowledgeNetwork className="h-auto w-full max-w-sm" />
              <p className="mt-2 text-center text-sm text-muted">K = knowledge · E = experience · V = values</p>
            </div>
          </div>
        </Section>

        {/* CTA */}
        <section className="px-4 pb-24 sm:px-6" aria-labelledby="cta-title">
          <div className="card-paper mx-auto grid max-w-6xl items-center gap-8 overflow-hidden p-8 sm:p-12 lg:grid-cols-2">
            <div>
              <p className="label-hand mb-2">Start your notebook</p>
              <h2 id="cta-title" className="text-3xl font-semibold sm:text-4xl">
                Teach your twin once. Let it mentor for years.
              </h2>
              <p className="mt-4 text-muted">
                Create your mentor profile in a few minutes, add a handful of experiences, and ask your first question.
              </p>
              <ButtonLink to={ctaTarget} size="lg" className="mt-6" icon={<Sparkles className="h-4 w-4" />}>
                Build Your Mentor
              </ButtonLink>
            </div>
            <visuals.classroom className="h-auto w-full" />
          </div>
        </section>
      </main>

      <footer className="border-t border-line bg-paper/70">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-8 text-sm text-muted sm:flex-row sm:px-6">
          <Brand />
          <p>PersonaTwin offers mentoring perspectives, not professional advice.</p>
          <p>© {new Date().getFullYear()} PersonaTwin</p>
        </div>
      </footer>
    </div>
  );
}
