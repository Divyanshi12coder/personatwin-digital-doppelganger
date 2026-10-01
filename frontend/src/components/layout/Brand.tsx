import { Link } from "react-router-dom";
import { cn } from "@/utils/format";

export function BrandMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={cn("h-9 w-9", className)} aria-hidden>
      <rect width="64" height="64" rx="16" fill="#4A2C1A" />
      <path d="M18 46c8-2 14-8 18-16l6-12 4 2-6 12c-4 9-11 15-20 17z" fill="#E7B84B" />
      <circle cx="44" cy="20" r="3" fill="#FFF9ED" />
      <path d="M14 50h22" stroke="#D4A017" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export function Brand({ to = "/", light = false }: { to?: string; light?: boolean }) {
  return (
    <Link to={to} className="group inline-flex items-center gap-2.5 rounded-lg" aria-label="PersonaTwin home">
      <BrandMark />
      <span className={cn("font-display text-xl font-semibold tracking-tight", light ? "text-cream" : "text-brown")}>
        Persona<span className="text-mustard">Twin</span>
      </span>
    </Link>
  );
}
