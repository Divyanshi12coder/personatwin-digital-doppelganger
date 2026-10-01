import { SendHorizonal } from "lucide-react";
import { useEffect, useRef, type KeyboardEvent } from "react";
import { cn } from "@/utils/format";

const MAX = 4000;

export function ChatInput({
  value,
  onChange,
  onSend,
  disabled,
  placeholder = "Ask your mentor anything…",
}: {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled?: boolean;
  placeholder?: string;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      if (!disabled && value.trim()) onSend();
    }
  };

  const tooLong = value.length > MAX;

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!disabled && value.trim() && !tooLong) onSend();
      }}
      className="card-paper flex items-end gap-2 p-2 pl-4 focus-within:ring-2 focus-within:ring-mustard/40"
    >
      <label htmlFor="chat-input" className="sr-only">
        Message your mentor
      </label>
      <textarea
        id="chat-input"
        ref={ref}
        rows={1}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder={placeholder}
        className="max-h-[200px] flex-1 resize-none bg-transparent py-2.5 text-[15px] leading-relaxed text-ink outline-none placeholder:text-muted/70"
        aria-describedby="chat-input-hint"
      />
      <div className="flex flex-col items-end gap-1 pb-1">
        {value.length > MAX * 0.8 && (
          <span className={cn("text-[11px] tabular-nums", tooLong ? "text-red-700" : "text-muted")}>
            {value.length}/{MAX}
          </span>
        )}
        <button
          type="submit"
          disabled={disabled || !value.trim() || tooLong}
          className="grid h-10 w-10 place-items-center rounded-xl bg-brown text-cream transition-colors hover:bg-brown-light disabled:cursor-not-allowed disabled:opacity-40"
          aria-label="Send message"
        >
          <SendHorizonal className="h-4 w-4" />
        </button>
      </div>
      <span id="chat-input-hint" className="sr-only">
        Press Enter to send, Shift plus Enter for a new line.
      </span>
    </form>
  );
}
