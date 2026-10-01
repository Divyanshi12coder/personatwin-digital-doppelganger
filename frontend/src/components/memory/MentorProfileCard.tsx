import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { Avatar, ProgressRing } from "@/components/ui/Feedback";
import { visuals } from "@/config/visuals";
import type { Overview } from "@/types/api";
import { humanize } from "@/utils/format";

export function MentorProfileCard({ profile }: { profile: Overview["profile"] }) {
  return (
    <div className="card-paper relative overflow-hidden p-6">
      <visuals.fountainPen className="pointer-events-none absolute -right-10 -top-3 w-48 rotate-[-14deg] opacity-15" />
      <div className="flex items-start gap-4">
        <Avatar name={profile.mentor_name} size="lg" />
        <div className="min-w-0 flex-1">
          <p className="label-hand">Your mentor</p>
          <h2 className="truncate text-2xl font-semibold">{profile.mentor_name ?? "Unnamed mentor"}</h2>
          <p className="mt-1 text-sm text-muted">
            {humanize(profile.communication_style)} · {humanize(profile.tone)}
          </p>
        </div>
        <ProgressRing value={profile.completeness} label="Profile completeness" />
      </div>
      {profile.bio && <p className="mt-4 line-clamp-3 text-sm text-ink/80">{profile.bio}</p>}
      <div className="mt-4 flex flex-wrap gap-1.5">
        {[...profile.expertise_areas, ...profile.values].slice(0, 8).map((t) => (
          <span key={t} className="chip">
            {t}
          </span>
        ))}
      </div>
      {profile.missing.length > 0 && (
        <div className="mt-5 rounded-xl border border-dashed border-gold bg-softgold/30 p-3">
          <p className="text-xs font-semibold text-brown">To make your twin sound more like you, add:</p>
          <p className="mt-1 text-xs text-chocolate">{profile.missing.join(" · ")}</p>
          <Link
            to="/app/personality"
            className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-chocolate underline decoration-mustard underline-offset-4"
          >
            Complete your profile <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      )}
    </div>
  );
}
