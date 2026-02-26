import { useEffect, useRef } from "react";

type Props = {
  values: number[];
};

export function WaveformCanvas({ values }: Props) {
  const ref = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) {
      return;
    }
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      return;
    }

    const { width, height } = canvas;
    ctx.clearRect(0, 0, width, height);
    ctx.strokeStyle = "rgba(128, 240, 255, 0.9)";
    ctx.lineWidth = 2;
    ctx.beginPath();

    const points = values.length > 1 ? values : [0.2, 0.3, 0.1, 0.25, 0.15];
    points.forEach((value, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * width;
      const y = height - value * height;
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();
  }, [values]);

  return <canvas ref={ref} className="waveform" width={420} height={90} />;
}
