import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type Props = PropsWithChildren<ButtonHTMLAttributes<HTMLButtonElement>>;

export function GlassButton({ children, className, ...rest }: Props) {
  return (
    <button className={`glass-button ${className ?? ""}`.trim()} {...rest}>
      {children}
    </button>
  );
}
