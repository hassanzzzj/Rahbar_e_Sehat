import type { ButtonHTMLAttributes, AnchorHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "emergency";
type Size = "sm" | "md" | "lg";

type BaseProps = {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  children: ReactNode;
};

type ButtonAsButton = BaseProps &
  ButtonHTMLAttributes<HTMLButtonElement> & { asChild?: false };

type ButtonAsAnchor = BaseProps &
  AnchorHTMLAttributes<HTMLAnchorElement> & { asChild: true };

type Props = ButtonAsButton | ButtonAsAnchor;

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    "bg-[#357A53] text-white hover:bg-[#276142] border border-[#276142] focus-visible:ring-2 focus-visible:ring-[#357A53] focus-visible:ring-offset-1",
  secondary:
    "bg-white text-[#333028] hover:bg-[#F2F0EC] border border-[#E5E1DA]",
  ghost:
    "bg-transparent text-[#66605A] hover:bg-[#F2F0EC] border border-transparent",
  danger:
    "bg-[#B52D24] text-white hover:bg-[#8F231C] border border-[#8F231C]",
  emergency:
    "bg-[#B52D24] text-white hover:bg-[#8F231C] border border-[#8F231C] emergency-pulse",
};

const SIZE_CLASSES: Record<Size, string> = {
  sm: "px-3 py-1.5 text-xs rounded-md gap-1",
  md: "px-4 py-2.5 text-sm rounded-lg gap-1.5",
  lg: "px-6 py-3.5 text-base rounded-xl gap-2",
};

function Spinner() {
  return (
    <svg
      className="animate-spin h-4 w-4 shrink-0"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

/**
 * Button / anchor primitive.
 * Pass `asChild` with a `<Link>` child to render as an anchor with button styling.
 */
export function Button(props: Props) {
  const { variant = "primary", size = "md", loading = false, children, ...rest } = props;
  const cls = [
    "interactive inline-flex items-center justify-center font-semibold transition-all duration-120 disabled:opacity-45 disabled:cursor-not-allowed disabled:pointer-events-none",
    VARIANT_CLASSES[variant],
    SIZE_CLASSES[size],
    rest.className ?? "",
  ].join(" ");

  const content = (
    <>
      {loading && <Spinner />}
      {children}
    </>
  );

  if (props.asChild) {
    const { asChild: _a, size: _s, loading: _l, ...anchorProps } = props as ButtonAsAnchor;
    return (
      <a {...anchorProps} className={cls}>
        {content}
      </a>
    );
  }

  const { asChild: _a, size: _s, loading: _l, ...buttonProps } = props as ButtonAsButton;
  return (
    <button type="button" {...buttonProps} className={cls}>
      {content}
    </button>
  );
}
