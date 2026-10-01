import { Info, Save, UserRound } from "lucide-react";
import { useEffect, useState } from "react";
import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer } from "recharts";
import {
  DEFAULT_PERSONALITY,
  PhilosophyFields,
  SliderFields,
  StyleFields,
  ValuesFields,
} from "@/components/persona/PersonaFields";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { ErrorState, LoadingState, PageHeader, ProgressRing } from "@/components/ui/Feedback";
import { Input, Textarea } from "@/components/ui/Field";
import { TagInput } from "@/components/ui/TagInput";
import { useOptions } from "@/context/OptionsContext";
import { useToast } from "@/context/ToastContext";
import { useAsync, useDocumentTitle } from "@/hooks/useAsync";
import { errorMessage } from "@/services/api";
import { profileApi } from "@/services/endpoints";
import type { MentorProfileInput, Personality, Profile } from "@/types/api";
import { cn } from "@/utils/format";

const SECTIONS = [
  { id: "style", label: "Style" },
  { id: "register", label: "Register" },
  { id: "values", label: "Values" },
  { id: "philosophy", label: "Philosophy" },
] as const;

function stripPersonality(p: Profile["personality"]): Personality {
  const { updated_at: _ignored, ...rest } = p;
  void _ignored;
  return { ...DEFAULT_PERSONALITY, ...rest };
}

export default function PersonalityPage() {
  useDocumentTitle("Personality");
  const toast = useToast();
  const { options } = useOptions();
  const profile = useAsync(() => profileApi.get(), []);
  const [mentor, setMentor] = useState<MentorProfileInput | null>(null);
  const [persona, setPersona] = useState<Personality | null>(null);
  const [savingMentor, setSavingMentor] = useState(false);
  const [savingPersona, setSavingPersona] = useState(false);
  const [section, setSection] = useState<(typeof SECTIONS)[number]["id"]>("style");

  useEffect(() => {
    if (!profile.data) return;
    const m = profile.data.mentor;
    setMentor({
      mentor_name: m?.mentor_name ?? "",
      bio: m?.bio ?? "",
      expertise_areas: m?.expertise_areas ?? [],
      mentoring_domains: m?.mentoring_domains ?? [],
    });
    setPersona(stripPersonality(profile.data.personality));
  }, [profile.data]);

  if (profile.error) return <ErrorState message={profile.error} onRetry={profile.reload} />;
  if (!profile.data || !mentor || !persona || !options) return <LoadingState label="Opening your persona notebook…" />;

  const saveMentor = async () => {
    if (!mentor.mentor_name.trim()) return toast.error("Your mentor needs a name.");
    setSavingMentor(true);
    try {
      profile.setData(await profileApi.updateMentor(mentor));
      toast.success("Mentor profile saved.");
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSavingMentor(false);
    }
  };

  const savePersona = async () => {
    setSavingPersona(true);
    try {
      profile.setData(await profileApi.updatePersonality(persona));
      toast.success("Persona updated — your next answers will use it.");
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSavingPersona(false);
    }
  };

  const radar = [
    { trait: "Formality", value: persona.formality },
    { trait: "Directness", value: persona.directness },
    { trait: "Warmth", value: persona.warmth },
    { trait: "Humor", value: persona.humor },
  ];

  return (
    <div>
      <PageHeader
        eyebrow="Persona memory"
        title="Personality profile"
        description="How your twin communicates. This is a configurable communication profile — not a psychological diagnosis or assessment."
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_340px]">
        <div className="space-y-6">
          <Card>
            <CardHeader title="Mentor profile" subtitle="Name, bio and expertise" icon={<UserRound className="h-5 w-5" />} />
            <div className="grid gap-4 md:grid-cols-2">
              <Input
                label="Mentor name"
                value={mentor.mentor_name}
                onChange={(e) => setMentor({ ...mentor, mentor_name: e.target.value })}
                maxLength={80}
                required
              />
              <TagInput
                label="Mentoring domains"
                value={mentor.mentoring_domains}
                onChange={(mentoring_domains) => setMentor({ ...mentor, mentoring_domains })}
                suggestions={options.mentoring_domains}
                max={9}
              />
              <Textarea
                label="Short bio"
                rows={3}
                value={mentor.bio}
                onChange={(e) => setMentor({ ...mentor, bio: e.target.value })}
                maxLength={2000}
                wrapperClassName="md:col-span-2"
              />
              <div className="md:col-span-2">
                <TagInput
                  label="Expertise areas"
                  value={mentor.expertise_areas}
                  onChange={(expertise_areas) => setMentor({ ...mentor, expertise_areas })}
                  max={15}
                />
              </div>
            </div>
            <div className="mt-5 flex justify-end">
              <Button onClick={() => void saveMentor()} loading={savingMentor} icon={<Save className="h-4 w-4" />}>
                Save profile
              </Button>
            </div>
          </Card>

          <Card padded={false}>
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 pt-4 sm:px-6">
              <div role="tablist" aria-label="Persona sections" className="-mb-px flex gap-1 overflow-x-auto">
                {SECTIONS.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    role="tab"
                    id={`tab-${s.id}`}
                    aria-selected={section === s.id}
                    aria-controls={`panel-${s.id}`}
                    onClick={() => setSection(s.id)}
                    className={cn(
                      "whitespace-nowrap border-b-2 px-3 py-2.5 text-sm font-medium",
                      section === s.id ? "border-mustard text-brown" : "border-transparent text-muted hover:text-brown",
                    )}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
            <div role="tabpanel" id={`panel-${section}`} aria-labelledby={`tab-${section}`} className="p-5 sm:p-6">
              {section === "style" && <StyleFields value={persona} onChange={setPersona} options={options.persona} />}
              {section === "register" && <SliderFields value={persona} onChange={setPersona} />}
              {section === "values" && <ValuesFields value={persona} onChange={setPersona} />}
              {section === "philosophy" && <PhilosophyFields value={persona} onChange={setPersona} />}
            </div>
            <div className="flex justify-end border-t border-line bg-paper/50 px-5 py-3 sm:px-6">
              <Button onClick={() => void savePersona()} loading={savingPersona} icon={<Save className="h-4 w-4" />}>
                Save persona
              </Button>
            </div>
          </Card>
        </div>

        <aside className="space-y-6 xl:sticky xl:top-8 xl:self-start">
          <Card>
            <div className="flex items-center gap-4">
              <ProgressRing value={profile.data.completeness} label="Profile completeness" />
              <div>
                <p className="font-display text-lg font-semibold text-brown">Profile completeness</p>
                <p className="text-xs text-muted">
                  {profile.data.missing.length ? `Missing: ${profile.data.missing.join(", ")}` : "Everything is filled in."}
                </p>
              </div>
            </div>
          </Card>
          <Card>
            <CardHeader title="Register at a glance" subtitle="Live preview of your sliders" />
            <div className="h-56" role="img" aria-label={radar.map((r) => `${r.trait} ${r.value}`).join(", ")}>
              <ResponsiveContainer>
                <RadarChart data={radar} outerRadius="72%">
                  <PolarGrid stroke="#E6D9BF" />
                  <PolarAngleAxis dataKey="trait" tick={{ fill: "#6B4226", fontSize: 12 }} />
                  <Radar dataKey="value" stroke="#D4A017" fill="#E7B84B" fillOpacity={0.45} isAnimationActive />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </Card>
          <div className="flex gap-3 rounded-xl border border-line bg-white/70 p-4 text-xs text-muted">
            <Info className="h-4 w-4 shrink-0 text-chocolate" aria-hidden />
            <p>
              Your persona shapes tone and structure only. Facts and personal stories always come from your Knowledge Vault and
              Experiences — never from these settings.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
