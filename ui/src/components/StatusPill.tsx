type Props = {
  state: "CONNECTED" | "DEGRADED" | "OFFLINE";
};

export function StatusPill({ state }: Props) {
  return <span className={`status-pill status-${state.toLowerCase()}`}>{state}</span>;
}
