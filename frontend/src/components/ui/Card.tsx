import type { ReactNode } from "react";

type CardVariant = "default" | "elevated" | "emergency" | "urgent" | "routine" | "flat";

interface Props {
  title?: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
  variant?: CardVariant;
  /** Left-border accent color (overrides variant border) */
  accentBorder?: boolean;
}

const VARIANT_CLASSES: Record<CardVariant, string> = {
  default:
    "bg-white border border-[#E5E1DA] rounded-xl shadow-card hover:shadow-card-hover transition-shadow duration-200",
  elevated:
    "bg-white border border-[#E5E1DA] rounded-xl shadow-card-hover",
  emergency:
    "bg-[#FDF2F1] border border-[#F4C1BE] rounded-xl shadow-card border-l-4 border-l-[#B52D24]",
  urgent:
    "bg-[#FDF8EE] border border-[#F5DFA0] rounded-xl shadow-card border-l-4 border-l-[#C47A18]",
  routine:
    "bg-[#EEF4F0] border border-[#B0D2BC] rounded-xl shadow-card border-l-4 border-l-[#357A53]",
  flat:
    "bg-[#F9F8F6] border border-[#E5E1DA] rounded-xl",
};

export function Card({
  title,
  children,
  footer,
  className = "",
  variant = "default",
  accentBorder = false,
}: Props) {
  return (
    <article
      className={`flex flex-col gap-3 p-5 ${VARIANT_CLASSES[variant]} ${
        accentBorder && variant === "default"
          ? "border-l-4 border-l-[#357A53]"
          : ""
      } ${className}`}
    >
      {title && (
        <header>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-[#66605A]">
            {title}
          </h2>
        </header>
      )}
      <div className="flex-1 text-sm text-[#333028]">{children}</div>
      {footer && (
        <footer className="border-t border-[#E5E1DA] pt-3 text-xs text-[#A8A098]">
          {footer}
        </footer>
      )}
    </article>
  );
}
