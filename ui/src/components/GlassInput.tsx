import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement> & { label?: string };
type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & { label?: string };

export function GlassInput({ label, className, ...rest }: InputProps) {
  return (
    <label className="field">
      {label && <span>{label}</span>}
      <input className={`glass-input ${className ?? ""}`.trim()} {...rest} />
    </label>
  );
}

export function GlassTextarea({ label, className, ...rest }: TextareaProps) {
  return (
    <label className="field">
      {label && <span>{label}</span>}
      <textarea className={`glass-input glass-textarea ${className ?? ""}`.trim()} {...rest} />
    </label>
  );
}
