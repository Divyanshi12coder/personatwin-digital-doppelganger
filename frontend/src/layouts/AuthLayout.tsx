import { motion } from "framer-motion";
import type { ReactNode } from "react";
import { StickyNote } from "@/components/illustrations/Illustrations";
import { Brand } from "@/components/layout/Brand";
import { visuals } from "@/config/visuals";

/** Split layout: form on paper, warm study-desk illustration on the side. */
export function AuthLayout({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="flex flex-col px-4 py-6 sm:px-10">
        <Brand />
        <main id="main" className="flex flex-1 items-center justify-center py-10">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="w-full max-w-md"
          >
            <h1 className="text-3xl font-semibold sm:text-4xl">{title}</h1>
            <p className="mt-2 text-muted">{subtitle}</p>
            <div className="mt-8">{children}</div>
          </motion.div>
        </main>
      </div>
      <aside className="relative hidden overflow-hidden bg-brown lg:block" aria-hidden>
        <div className="dot-grid absolute inset-0 opacity-30" />
        <div className="absolute left-1/2 top-1/2 h-[420px] w-[420px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gold/25 blur-3xl" />
        <visuals.lamp className="absolute right-16 top-0 h-56 w-44" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative">
            <visuals.notebook className="w-72 -rotate-6 drop-shadow-2xl" />
            <visuals.fountainPen className="absolute -bottom-6 -right-24 w-72 -rotate-[24deg] drop-shadow-xl" />
            <div className="absolute -left-36 top-10">
              <StickyNote text="Write it down once. Learn from it forever." rotate={-6} />
            </div>
            <div className="absolute -right-32 -top-8">
              <StickyNote text="What would you tell your younger self?" rotate={5} color="#FFF9ED" />
            </div>
          </div>
        </div>
        <p className="absolute inset-x-0 bottom-10 text-center font-hand text-2xl text-gold">
          your knowledge · your stories · your voice
        </p>
      </aside>
    </div>
  );
}
