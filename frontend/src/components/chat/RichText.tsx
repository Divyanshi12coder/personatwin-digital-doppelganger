import { Fragment, type ReactNode } from "react";

/*
 * A deliberately tiny, safe renderer for mentor replies. It builds React
 * elements (never raw HTML), so model output can't inject markup.
 * Supports paragraphs, "- " and "1. " lists, **bold**, _italic_, `code`
 * and citation labels like [K1] / [E2] / [C1].
 */

const INLINE_RE = /(\*\*[^*]+\*\*|_[^_\n]+_|`[^`]+`|\[[KEC]\d{1,2}\])/g;

function renderInline(text: string, onCite?: (label: string) => void, keyPrefix = ""): ReactNode[] {
  return text.split(INLINE_RE).map((part, i) => {
    const key = `${keyPrefix}-${i}`;
    if (!part) return null;
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={key}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("_") && part.endsWith("_") && part.length > 2) return <em key={key}>{part.slice(1, -1)}</em>;
    if (part.startsWith("`") && part.endsWith("`"))
      return (
        <code key={key} className="rounded bg-paper px-1 py-0.5 text-[0.85em]">
          {part.slice(1, -1)}
        </code>
      );
    const cite = /^\[([KEC]\d{1,2})\]$/.exec(part);
    if (cite) {
      const label = cite[1];
      const tone = label.startsWith("E") ? "bg-brown text-cream" : label.startsWith("K") ? "bg-softgold text-brown" : "bg-paper text-chocolate";
      return (
        <button
          key={key}
          type="button"
          onClick={() => onCite?.(label)}
          className={`mx-0.5 inline-flex -translate-y-px items-center rounded-md px-1.5 text-[11px] font-semibold leading-5 ${tone} hover:ring-2 hover:ring-mustard/50`}
          aria-label={`Show memory ${label}`}
        >
          {label}
        </button>
      );
    }
    return <Fragment key={key}>{part}</Fragment>;
  });
}

export function RichText({ text, onCite }: { text: string; onCite?: (label: string) => void }) {
  const blocks = text.replace(/\r\n/g, "\n").split(/\n{2,}/);
  return (
    <div className="prose-mentor text-[15px] leading-relaxed text-ink/90">
      {blocks.map((block, bi) => {
        const lines = block.split("\n").filter((l) => l.trim());
        if (!lines.length) return null;
        const bullet = lines.filter((l) => /^\s*[-*]\s+/.test(l));
        const numbered = lines.filter((l) => /^\s*\d+[.)]\s+/.test(l));
        // A header line followed by list items.
        const header = (bullet.length || numbered.length) && lines.length > (bullet.length || numbered.length) ? lines[0] : null;
        if (bullet.length && bullet.length >= lines.length - (header ? 1 : 0)) {
          return (
            <Fragment key={bi}>
              {header && <p>{renderInline(header, onCite, `h${bi}`)}</p>}
              <ul>
                {bullet.map((l, li) => (
                  <li key={li}>{renderInline(l.replace(/^\s*[-*]\s+/, ""), onCite, `${bi}-${li}`)}</li>
                ))}
              </ul>
            </Fragment>
          );
        }
        if (numbered.length && numbered.length >= lines.length - (header ? 1 : 0)) {
          return (
            <Fragment key={bi}>
              {header && <p>{renderInline(header, onCite, `h${bi}`)}</p>}
              <ol>
                {numbered.map((l, li) => (
                  <li key={li}>{renderInline(l.replace(/^\s*\d+[.)]\s+/, ""), onCite, `${bi}-${li}`)}</li>
                ))}
              </ol>
            </Fragment>
          );
        }
        return (
          <p key={bi}>
            {lines.map((l, li) => (
              <Fragment key={li}>
                {li > 0 && <br />}
                {renderInline(l.replace(/^#{1,6}\s+/, ""), onCite, `${bi}-${li}`)}
              </Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
}
