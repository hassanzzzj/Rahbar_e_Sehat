import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

/* ── Shared label/hint/error wrapper ───────────────────────── */
interface WrapperProps {
  label: string;
  error?: string;
  hint?: string;
  inputId: string;
  hintId: string;
  errorId: string;
  children: React.ReactNode;
  required?: boolean;
}

function FieldWrapper({ label, error, hint, inputId, hintId, errorId, children, required }: WrapperProps) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={inputId} className="text-sm font-semibold text-[#333028]">
        {label}
        {required && <span className="ml-1 text-[#B52D24]" aria-hidden="true">*</span>}
      </label>
      {hint && (
        <span id={hintId} className="text-xs text-[#A8A098]">
          {hint}
        </span>
      )}
      {children}
      {error && (
        <span id={errorId} role="alert" className="flex items-center gap-1 text-xs text-[#B52D24]">
          {error}
        </span>
      )}
    </div>
  );
}

/* ── Input ──────────────────────────────────────────────────── */
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
}

export function Input({ label, error, hint, id, className = "", required, ...rest }: InputProps) {
  const inputId = id ?? `input-${label.toLowerCase().replace(/\s+/g, "-")}`;
  const hintId = `${inputId}-hint`;
  const errorId = `${inputId}-error`;

  return (
    <FieldWrapper
      label={label}
      error={error}
      hint={hint}
      inputId={inputId}
      hintId={hintId}
      errorId={errorId}
      required={required}
    >
      <input
        id={inputId}
        required={required}
        aria-describedby={
          [hint && hintId, error && errorId].filter(Boolean).join(" ") || undefined
        }
        aria-invalid={error ? "true" : undefined}
        className={[
          "h-11 w-full rounded-xl border bg-white px-3 text-sm text-[#1A1815] placeholder-[#A8A098]",
          "transition-colors duration-120",
          "focus:outline-none focus:ring-2 focus:ring-[#357A53] focus:ring-offset-0 focus:border-[#357A53]",
          "disabled:bg-[#F2F0EC] disabled:cursor-not-allowed disabled:opacity-60",
          error ? "border-[#B52D24]" : "border-[#E5E1DA] hover:border-[#CCC7BC]",
          className,
        ].join(" ")}
        {...rest}
      />
    </FieldWrapper>
  );
}

/* ── Textarea ───────────────────────────────────────────────── */
interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
  hint?: string;
}

export function Textarea({ label, error, hint, id, className = "", required, ...rest }: TextareaProps) {
  const inputId = id ?? `textarea-${label.toLowerCase().replace(/\s+/g, "-")}`;
  const hintId = `${inputId}-hint`;
  const errorId = `${inputId}-error`;

  return (
    <FieldWrapper
      label={label}
      error={error}
      hint={hint}
      inputId={inputId}
      hintId={hintId}
      errorId={errorId}
      required={required}
    >
      <textarea
        id={inputId}
        required={required}
        aria-describedby={
          [hint && hintId, error && errorId].filter(Boolean).join(" ") || undefined
        }
        aria-invalid={error ? "true" : undefined}
        className={[
          "w-full rounded-xl border bg-white px-3 py-3 text-sm text-[#1A1815] placeholder-[#A8A098]",
          "min-h-[120px] resize-y leading-relaxed",
          "transition-colors duration-120",
          "focus:outline-none focus:ring-2 focus:ring-[#357A53] focus:ring-offset-0 focus:border-[#357A53]",
          "disabled:bg-[#F2F0EC] disabled:cursor-not-allowed disabled:opacity-60",
          error ? "border-[#B52D24]" : "border-[#E5E1DA] hover:border-[#CCC7BC]",
          className,
        ].join(" ")}
        {...rest}
      />
    </FieldWrapper>
  );
}
