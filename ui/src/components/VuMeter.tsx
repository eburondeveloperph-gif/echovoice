type Props = {
  level: number;
};

export function VuMeter({ level }: Props) {
  const percentage = Math.round(Math.max(0, Math.min(1, level)) * 100);
  return (
    <div className="vu-meter" aria-label="VU Meter">
      <div className="vu-meter-fill" style={{ width: `${percentage}%` }} />
      <span>{percentage}%</span>
    </div>
  );
}
