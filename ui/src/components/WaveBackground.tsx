export function WaveBackground() {
  return (
    <div className="wave-bg" role="presentation" aria-hidden>
      <div className="wave-gradient" />
      <svg className="wave-svg wave-a" viewBox="0 0 1600 360" preserveAspectRatio="none">
        <path d="M0,190 C200,130 400,250 600,190 C800,130 1000,250 1200,190 C1400,130 1500,220 1600,180 L1600,360 L0,360 Z" />
      </svg>
      <svg className="wave-svg wave-b" viewBox="0 0 1600 360" preserveAspectRatio="none">
        <path d="M0,220 C220,160 380,280 620,220 C860,160 980,280 1260,220 C1440,180 1500,260 1600,220 L1600,360 L0,360 Z" />
      </svg>
    </div>
  );
}
