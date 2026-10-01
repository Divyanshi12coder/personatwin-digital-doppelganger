import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, ArrowRight, Check, Sparkles } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  DEFAULT_PERSONALITY,
  PERSONA_LABELS,
  PhilosophyFields,
  SliderFields,
  StyleFields,
  ValuesFields,
} from "@/components/persona/PersonaFields";
import { Brand } from "@/components/layout/Brand";
import { Button } from "@/components/ui/Button";
import { ErrorState, LoadingState } from "@/components/ui/Feedback";
import { Input, Textarea } from "@/components/ui/Field";
import { TagInput } from "@/components/ui/TagInput";
import { useAuth } from "@/context/AuthContext";
import { useOptions } from "@/context/OptionsContext";
import { useToast } from "@/context/ToastContext";
import { useDocumentTitle } from "@/hooks/useAsync";
import { errorMessage } from "@/services/api";
import { profileApi } from "@/services/endpoints";
import type { MentorProfileInput, PersonaOptionKey, Personality } from "@/types/api";
import { cn, humanize } from "@/utils/format";

const STEPS = [
  { key: "basics", title: "The basics", hint: "Who is your mentor?" },
  { key: "voice", title: "Voice & style", hint: "How does your mentor communicate?" },
  { key: "philosophy", title: "Mentoring philosophy", hint: "What do you believe about growth?" },
  { key: "review", title: "Review", hint: "Check everything before we save it." },
] as const;

export default function OnboardingPage() {
  useDocumentTitle("Create your mentor");
  const { user, setUser } = useAuth();
  const { options, error: optionsError } = useOptions();
  const toast = useToast();
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mentor, setMentor] = useState<MentorProfileInput>({
    mentor_name: user ? `${user.full_name.split(" ")[0]}'s Twin` : "",
    bio: "",
    expertise_areas: [],
    mentoring_domains: [],
  });
  const [personality, setPersonality] = useState<Personality>(DEFAULT_PERSONALITY);

  const basicsValid = mentor.mentor_name.trim().length > 0;

  const next = () => {
    setError(null);
    if (step === 0 && !basicsValid) {
      setError("Give your mentor a name to continue.");
      return;
    }
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const finish = async () => {
    setSaving(true);
    setError(null);
    try {
      await profileApi.onboarding(mentor, personality);
      if (user) setUser({ ...user, onboarding_completed: true });
      toast.success("Your mentor is ready. Add a few memories to make it truly yours.");
      navigate("/app", { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  if (optionsError) return <div className="mx-auto max-w-xl p-6"><ErrorState message="Couldn't load the profile options. Is the API running?" onRetry={() => window.location.reload()} /></div>;
  if (!options) return <LoadingState label="Preparing your notebook…" className="min-h-screen" />;

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-cream/90 backdrop-blur">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4 sm:px-6">
          <Brand />
          <span className="text-sm text-muted">
            Step {step + 1} of {STEPS.length}
          </span>
        </div>
      </header>

      <main id="main" className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-12">
        <ol className="mb-8 grid grid-cols-4 gap-2" aria-label="Onboarding progress">
          {STEPS.map((s, i) => (
            <li key={s.key} aria-current={i === step ? "step" : undefined}>
              <div className={cn("h-1.5 rounded-full transition-colors", i <= step ? "bg-mustard" : "bg-line")} />
              <p className={cn("mt-2 hidden text-xs font-medium sm:block", i === step ? "text-brown" : "text-muted")}>{s.title}</p>
            </li>
          ))}
        </ol>

        <p className="label-hand">{STEPS[step].hint}</p>
        <h1 className="mb-6 text-3xl font-semibold sm:text-4xl">{STEPS[step].title}</h1>

        {error && (
          <div role="alert" className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -24 }}
            transition={{ duration: 0.25 }}
            className="card-paper space-y-6 p-5 sm:p-8"
          >
            {step === 0 && (
              <>
                <Input
                  label="Mentor name"
                  value={mentor.mentor_name}
                  onChange={(e) => setMentor({ ...mentor, mentor_name: e.target.value })}
                  maxLength={80}
                  required
                  hint="How your twin introduces itself."
                />
                <Textarea
                  label="Short bio"
                  rows={3}
                  maxLength={2000}
                  value={mentor.bio}
                  onChange={(e) => setMentor({ ...mentor, bio: e.target.value })}
                  placeholder="Engineer turned teacher. I've spent ten years helping people learn hard things…"
                />
                <TagInput
                  label="Expertise areas"
                  value={mentor.expertise_areas}
                  onChange={(expertise_areas) => setMentor({ ...mentor, expertise_areas })}
                  placeholder="e.g. Product design"
                  max={15}
                />
                <TagInput
                  label="Preferred mentoring domains"
                  value={mentor.mentoring_domains}
                  onChange={(mentoring_domains) => setMentor({ ...mentor, mentoring_domains })}
                  suggestions={options.mentoring_domains}
                  max={9}
                />
              </>
            )}

            {step === 1 && (
              <>
                <StyleFields value={personality} onChange={setPersonality} options={options.persona} />
                <div className="border-t border-line pt-6">
                  <h2 className="mb-4 text-lg font-semibold">Fine-tune the register</h2>
                  <SliderFields value={personality} onChange={setPersonality} />
                </div>
                <div className="border-t border-line pt-6">
                  <ValuesFields value={personality} onChange={setPersonality} />
                </div>
              </>
            )}

            {step === 2 && <PhilosophyFields value={personality} onChange={setPersonality} />}

            {step === 3 && (
              <div className="grid gap-6 md:grid-cols-2">
                <div>
                  <p className="label-hand">Mentor</p>
                  <h2 className="text-2xl font-semibold">{mentor.mentor_name}</h2>
                  <p className="mt-2 text-sm text-muted">{mentor.bio || "No bio yet."}</p>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {[...mentor.expertise_areas, ...mentor.mentoring_domains].map((t) => (
                      <span key={t} className="chip">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
                <dl className="space-y-2 text-sm">
                  {(Object.keys(PERSONA_LABELS) as PersonaOptionKey[]).map((k) => (
                    <div key={k} className="flex justify-between gap-4 border-b border-dashed border-line pb-1.5">
                      <dt className="text-muted">{PERSONA_LABELS[k]}</dt>
                      <dd className="font-medium text-brown">{humanize(personality[k])}</dd>
                    </div>
                  ))}
                  <div className="flex justify-between gap-4">
                    <dt className="text-muted">Values</dt>
                    <dd className="text-right font-medium text-brown">{personality.values.join(", ") || "—"}</dd>
                  </div>
                </dl>
                <p className="rounded-xl bg-paper p-4 text-xs text-muted md:col-span-2">
                  This is a communication profile you control — not a psychological assessment. You can change any of it
                  later from the Personality page.
                </p>
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        <div className="mt-6 flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0}
            icon={<ArrowLeft className="h-4 w-4" />}
          >
            Back
          </Button>
          {step < STEPS.length - 1 ? (
            <Button onClick={next} disabled={step === 0 && !basicsValid}>
              Continue <ArrowRight className="h-4 w-4" />
            </Button>
          ) : (
            <Button variant="accent" onClick={() => void finish()} loading={saving} icon={saving ? undefined : <Check className="h-4 w-4" />}>
              Create my mentor <Sparkles className="h-4 w-4" />
            </Button>
          )}
        </div>
      </main>
    </div>
  );
}
