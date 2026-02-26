import type { PropsWithChildren, ReactNode } from "react";

type Props = PropsWithChildren<{
  title?: string;
  actions?: ReactNode;
  className?: string;
}>;

export function GlassCard({ title, actions, className, children }: Props) {
  return (
    <section className={`glass-card ${className ?? ""}`.trim()}>
      {(title || actions) && (
        <header className="glass-card-header">
          {title && <h3>{title}</h3>}
          {actions}
        </header>
      )}
      <div className="glass-card-body">{children}</div>
    </section>
  );
}
