import { motion, type HTMLMotionProps } from "framer-motion";
import type { ReactNode } from "react";
import { cn } from "@/utils/format";

interface CardProps extends HTMLMotionProps<"div"> {
  padded?: boolean;
  ruled?: boolean;
  animate?: boolean;
}

/** Notebook-paper card. Entrance animation is subtle and disabled for reduced motion by CSS. */
export function Card({ padded = true, ruled = false, animate = true, className, children, ...rest }: CardProps) {
  return (
    <motion.div
      initial={animate ? { opacity: 0, y: 10 } : false}
      animate={animate ? { opacity: 1, y: 0 } : undefined}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={cn("card-paper min-w-0", padded && "p-5 sm:p-6", ruled && "ruled", className)}
      {...rest}
    >
      {children}
    </motion.div>
  );
}

export function CardHeader({
  title,
  subtitle,
  action,
  icon,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="mb-4 flex items-start justify-between gap-3">
      <div className="flex min-w-0 items-start gap-3">
        {icon && (
          <span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-softgold text-chocolate">{icon}</span>
        )}
        <div className="min-w-0">
          <h2 className="text-lg font-semibold leading-tight">{title}</h2>
          {subtitle && <p className="mt-0.5 text-sm text-muted">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
  );
}
