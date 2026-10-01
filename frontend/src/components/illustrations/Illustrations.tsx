/*
 * Original, hand-built SVG illustrations for PersonaTwin's "mentor's study" look.
 * They are local (no external image hosts, no licensing questions), themeable,
 * crisp at any size, and decorative — every one is aria-hidden by default.
 * The registry in src/config/visuals.ts is the single place pages pick them from.
 */
import { motion, useReducedMotion } from "framer-motion";
import type { SVGProps } from "react";

type IllustrationProps = SVGProps<SVGSVGElement> & { title?: string };

const a11y = (title?: string) =>
  title ? { role: "img" as const, "aria-label": title } : { "aria-hidden": true as const, focusable: "false" as const };

export function FountainPen({ title, ...props }: IllustrationProps) {
  return (
    <svg viewBox="0 0 240 60" fill="none" {...a11y(title)} {...props}>
      <defs>
        <linearGradient id="pen-body" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#6B4226" />
          <stop offset="0.5" stopColor="#4A2C1A" />
          <stop offset="1" stopColor="#2E1B10" />
        </linearGradient>
        <linearGradient id="pen-gold" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#F8E8B0" />
          <stop offset="0.5" stopColor="#E7B84B" />
          <stop offset="1" stopColor="#B3860F" />
        </linearGradient>
      </defs>
      <path d="M58 18h126c8 0 14 5 14 12s-6 12-14 12H58z" fill="url(#pen-body)" />
      <rect x="150" y="18" width="8" height="24" fill="url(#pen-gold)" />
      <rect x="164" y="18" width="3" height="24" fill="url(#pen-gold)" />
      <path d="M100 14h46a4 4 0 0 1 4 4v2h-54v-2a4 4 0 0 1 4-4z" fill="url(#pen-gold)" />
      <path d="M58 18 34 24l-4 6 4 6 24 6z" fill="#2E1B10" />
      <path d="M34 24 6 30l28 6z" fill="url(#pen-gold)" />
      <path d="M8 30h22" stroke="#4A2C1A" strokeWidth="1.2" />
      <circle cx="26" cy="30" r="1.6" fill="#4A2C1A" />
      <path d="M70 23h70" stroke="#fff" strokeOpacity="0.18" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function Pencil({ title, ...props }: IllustrationProps) {
  return (
    <svg viewBox="0 0 220 40" fill="none" {...a11y(title)} {...props}>
      <path d="M40 8h140v24H40z" fill="#D4A017" />
      <path d="M40 8h140v8H40z" fill="#E7B84B" />
      <path d="M40 24h140v8H40z" fill="#B3860F" />
      <path d="M180 8h14v24h-14z" fill="#C9C2B4" />
      <path d="M184 8v24M189 8v24" stroke="#9E978A" strokeWidth="1.5" />
      <path d="M194 8h12a6 6 0 0 1 6 6v12a6 6 0 0 1-6 6h-12z" fill="#D98C8C" />
      <path d="M40 8 12 20l28 12z" fill="#F3D9A8" />
      <path d="M12 20l10-4.3v8.6z" fill="#241A14" />
    </svg>
  );
}

export function Notebook({ title, lines = 9, ...props }: IllustrationProps & { lines?: number }) {
  return (
    <svg viewBox="0 0 260 320" fill="none" {...a11y(title)} {...props}>
      <rect x="18" y="12" width="232" height="300" rx="10" fill="#6B4226" />
      <rect x="28" y="8" width="226" height="298" rx="8" fill="#FFF9ED" stroke="#E6D9BF" />
      <path d="M62 8v298" stroke="#D4A017" strokeOpacity="0.55" strokeWidth="2" />
      {Array.from({ length: lines }).map((_, i) => (
        <path key={i} d={`M36 ${60 + i * 26}h210`} stroke="#806B5A" strokeOpacity="0.18" />
      ))}
      {Array.from({ length: 10 }).map((_, i) => (
        <g key={i}>
          <circle cx="28" cy={30 + i * 28} r="6" fill="#F7F1E3" stroke="#806B5A" strokeOpacity="0.4" />
          <path d={`M14 ${30 + i * 28}h18`} stroke="#4A2C1A" strokeWidth="3" strokeLinecap="round" />
        </g>
      ))}
      <path
        d="M76 52c10-6 18 6 28 0s18-6 26 0 16 4 24-2M76 78c14-4 22 4 34 0s20-4 30 2M76 104c8-4 16 4 26 0"
        stroke="#4A2C1A"
        strokeWidth="2.2"
        strokeLinecap="round"
        opacity="0.75"
      />
      <path d="M76 156c12-5 20 5 32 0s22-4 32 0 14 3 22-1M76 182c10-4 18 4 28 0" stroke="#6B4226" strokeWidth="2" strokeLinecap="round" opacity="0.6" />
      <circle cx="200" cy="230" r="22" stroke="#D4A017" strokeWidth="2.5" strokeDasharray="4 5" />
      <path d="M192 230l6 6 12-14" stroke="#D4A017" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function StickyNote({
  text,
  color = "#F8E8B0",
  rotate = -3,
  className,
}: {
  text: string;
  color?: string;
  rotate?: number;
  className?: string;
}) {
  return (
    <div
      aria-hidden
      className={`relative w-40 select-none p-4 pb-6 font-hand text-xl leading-snug text-brown shadow-paper ${className ?? ""}`}
      style={{ background: color, transform: `rotate(${rotate}deg)`, clipPath: "polygon(0 0,100% 0,100% 88%,88% 100%,0 100%)" }}
    >
      <span className="absolute -top-2 left-1/2 h-4 w-14 -translate-x-1/2 rotate-2 bg-white/60 shadow-sm" />
      {text}
    </div>
  );
}

export function OpenBook({ title, ...props }: IllustrationProps) {
  return (
    <svg viewBox="0 0 300 180" fill="none" {...a11y(title)} {...props}>
      <path d="M150 40c-30-18-80-22-130-14v134c50-8 100-4 130 14z" fill="#FFF9ED" stroke="#E6D9BF" />
      <path d="M150 40c30-18 80-22 130-14v134c-50-8-100-4-130 14z" fill="#F7F1E3" stroke="#E6D9BF" />
      <path d="M150 40v134" stroke="#6B4226" strokeWidth="2" />
      <path d="M14 30v136c52-8 104-4 136 16 32-20 84-24 136-16V30" stroke="#6B4226" strokeWidth="6" strokeLinecap="round" />
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <g key={i} stroke="#806B5A" strokeOpacity="0.35" strokeWidth="2" strokeLinecap="round">
          <path d={`M36 ${58 + i * 16}c30-3 60-2 96 8`} />
          <path d={`M168 ${66 + i * 16}c36-10 66-11 96-8`} />
        </g>
      ))}
      <path d="M226 26v36l9-7 9 7V24" fill="#D4A017" />
    </svg>
  );
}

export function Chalkboard({ title, ...props }: IllustrationProps) {
  return (
    <svg viewBox="0 0 360 230" fill="none" {...a11y(title)} {...props}>
      <rect x="6" y="6" width="348" height="200" rx="10" fill="#6B4226" />
      <rect x="18" y="18" width="324" height="176" rx="4" fill="#2F3A2F" />
      <rect x="18" y="18" width="324" height="176" rx="4" fill="url(#chalk-dust)" opacity="0.4" />
      <defs>
        <radialGradient id="chalk-dust" cx="0.3" cy="0.3" r="0.9">
          <stop offset="0" stopColor="#ffffff" stopOpacity="0.18" />
          <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
        </radialGradient>
      </defs>
      <g stroke="#F7F1E3" strokeWidth="2.2" strokeLinecap="round" opacity="0.9">
        <circle cx="90" cy="80" r="22" />
        <circle cx="200" cy="60" r="16" />
        <circle cx="260" cy="130" r="22" />
        <circle cx="130" cy="150" r="16" />
        <path d="M110 70l74-6M210 72l38 42M146 146l92-10M98 101l22 34" strokeDasharray="5 6" />
      </g>
      <g fill="#E7B84B">
        <circle cx="90" cy="80" r="6" />
        <circle cx="260" cy="130" r="6" />
      </g>
      <path d="M40 40c12-6 20 6 30 0" stroke="#F8E8B0" strokeWidth="2" strokeLinecap="round" />
      <rect x="40" y="206" width="280" height="10" rx="3" fill="#4A2C1A" />
      <rect x="70" y="200" width="22" height="6" rx="2" fill="#FFF9ED" />
      <rect x="100" y="201" width="16" height="5" rx="2" fill="#F8E8B0" />
    </svg>
  );
}

export function MentorPortrait({ title, ...props }: IllustrationProps) {
  return (
    <svg viewBox="0 0 200 200" fill="none" {...a11y(title)} {...props}>
      <circle cx="100" cy="100" r="96" fill="#F8E8B0" />
      <path d="M36 180c8-40 36-60 64-60s56 20 64 60" fill="#6B4226" />
      <path d="M86 122l14 22 14-22" fill="#FFF9ED" />
      <path d="M100 144v30" stroke="#D4A017" strokeWidth="5" />
      <circle cx="100" cy="82" r="34" fill="#E9C9A0" />
      <path d="M66 78c0-26 18-40 36-40s34 14 34 36c-10-12-26-16-44-14-10 1-20 8-26 18z" fill="#4A2C1A" />
      <g stroke="#241A14" strokeWidth="2.5">
        <circle cx="87" cy="86" r="9" />
        <circle cx="113" cy="86" r="9" />
        <path d="M96 86h8" />
      </g>
      <path d="M90 104c6 5 14 5 20 0" stroke="#4A2C1A" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

export function DeskLamp({ title, ...props }: IllustrationProps) {
  return (
    <svg viewBox="0 0 160 200" fill="none" {...a11y(title)} {...props}>
      <defs>
        <radialGradient id="lamp-glow" cx="0.5" cy="0.2" r="0.8">
          <stop offset="0" stopColor="#F8E8B0" stopOpacity="0.9" />
          <stop offset="1" stopColor="#F8E8B0" stopOpacity="0" />
        </radialGradient>
      </defs>
      <path d="M40 60 0 200h160L120 60z" fill="url(#lamp-glow)" />
      <path d="M50 30h60l18 34H32z" fill="#4A2C1A" />
      <path d="M58 30h44l-6-12H64z" fill="#6B4226" />
      <ellipse cx="80" cy="64" rx="48" ry="5" fill="#E7B84B" />
      <path d="M80 18V2" stroke="#6B4226" strokeWidth="4" />
    </svg>
  );
}

/** Animated knowledge graph — the "AI" half of the brand. */
export function KnowledgeNetwork({ title, className }: { title?: string; className?: string }) {
  const reduce = useReducedMotion();
  const nodes = [
    { x: 60, y: 60, r: 9, label: "K" },
    { x: 170, y: 40, r: 7, label: "" },
    { x: 250, y: 90, r: 10, label: "E" },
    { x: 120, y: 140, r: 14, label: "" },
    { x: 220, y: 180, r: 8, label: "V" },
    { x: 60, y: 200, r: 7, label: "" },
    { x: 290, y: 200, r: 6, label: "" },
  ];
  const links = [
    [0, 3],
    [1, 3],
    [2, 3],
    [3, 4],
    [3, 5],
    [1, 2],
    [4, 6],
    [0, 1],
  ];
  return (
    <svg viewBox="0 0 340 240" fill="none" className={className} {...a11y(title)}>
      {links.map(([a, b], i) => (
        <motion.line
          key={i}
          x1={nodes[a].x}
          y1={nodes[a].y}
          x2={nodes[b].x}
          y2={nodes[b].y}
          stroke="#6B4226"
          strokeOpacity="0.35"
          strokeWidth="1.5"
          strokeDasharray="4 5"
          initial={{ pathLength: reduce ? 1 : 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.2, delay: i * 0.12 }}
        />
      ))}
      {!reduce &&
        links.slice(0, 4).map(([a, b], i) => (
          <motion.circle
            key={`p${i}`}
            r="3"
            fill="#D4A017"
            initial={{ cx: nodes[a].x, cy: nodes[a].y, opacity: 0 }}
            animate={{ cx: [nodes[a].x, nodes[b].x], cy: [nodes[a].y, nodes[b].y], opacity: [0, 1, 0] }}
            transition={{ duration: 2.4, repeat: Infinity, delay: 1 + i * 0.6, ease: "easeInOut" }}
          />
        ))}
      {nodes.map((n, i) => (
        <g key={i}>
          <circle cx={n.x} cy={n.y} r={n.r + 6} fill="#F8E8B0" opacity="0.6" />
          <circle cx={n.x} cy={n.y} r={n.r} fill={i === 3 ? "#4A2C1A" : "#FFF9ED"} stroke="#6B4226" strokeWidth="2" />
          {n.label && (
            <text x={n.x} y={n.y + 4} textAnchor="middle" fontSize="10" fontWeight="700" fill="#6B4226">
              {n.label}
            </text>
          )}
        </g>
      ))}
      <circle cx="120" cy="140" r="4" fill="#E7B84B" />
    </svg>
  );
}

/** A small classroom vignette: board, desk, books, apple. */
export function ClassroomScene({ title, className }: { title?: string; className?: string }) {
  return (
    <svg viewBox="0 0 420 260" fill="none" className={className} {...a11y(title)}>
      <rect x="0" y="0" width="420" height="260" rx="18" fill="#F7F1E3" />
      <rect x="40" y="28" width="230" height="130" rx="6" fill="#6B4226" />
      <rect x="50" y="38" width="210" height="110" rx="3" fill="#2F3A2F" />
      <path d="M70 70c16-8 28 8 44 0s28-8 40 0M70 96c12-5 22 5 34 0M70 122h70" stroke="#F7F1E3" strokeWidth="2.5" strokeLinecap="round" opacity="0.85" />
      <circle cx="220" cy="92" r="20" stroke="#E7B84B" strokeWidth="2.5" />
      <path d="M212 92l6 6 12-12" stroke="#E7B84B" strokeWidth="3" strokeLinecap="round" />
      <rect x="0" y="200" width="420" height="60" fill="#E6D9BF" />
      <rect x="230" y="170" width="170" height="14" rx="4" fill="#4A2C1A" />
      <rect x="244" y="184" width="10" height="60" fill="#4A2C1A" />
      <rect x="376" y="184" width="10" height="60" fill="#4A2C1A" />
      <rect x="250" y="146" width="52" height="12" rx="2" fill="#D4A017" />
      <rect x="254" y="134" width="46" height="12" rx="2" fill="#6B4226" />
      <rect x="248" y="158" width="58" height="12" rx="2" fill="#806B5A" />
      <circle cx="350" cy="158" r="11" fill="#B4442C" />
      <path d="M350 147c0-6 4-9 8-10" stroke="#4A2C1A" strokeWidth="2" strokeLinecap="round" />
      <path d="M352 146c4-4 9-3 11 0-4 3-8 3-11 0z" fill="#5E7A3A" />
      <g transform="translate(300 40) rotate(4)">
        <rect width="74" height="64" fill="#F8E8B0" />
        <path d="M10 22h50M10 36h40M10 50h30" stroke="#6B4226" strokeWidth="2" strokeLinecap="round" opacity="0.6" />
      </g>
    </svg>
  );
}

export function Signature({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 220 60" fill="none" className={className} aria-hidden>
      <path
        d="M6 42c18-30 30-30 30-10s-8 24 4 6 22-26 26-8-4 18 10 6 20-18 30-4 18 10 34-6 30-12 40 2 26 8"
        stroke="#6B4226"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
