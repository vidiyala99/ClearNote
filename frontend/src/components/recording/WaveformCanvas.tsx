import { useEffect, useRef } from "react";

interface WaveformCanvasProps {
  analyser: AnalyserNode | null;
  status: string;
}

export default function WaveformCanvas({ analyser, status }: WaveformCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!analyser || status !== "recording") return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    let animationId: number;

    const draw = () => {
      animationId = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(dataArray);

      // slate-100 background
      ctx.fillStyle = "#f1f5f9";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 2.5;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = dataArray[i] / 2;
        // cyan-600 (#0891B2) → teal-500 (#14b8a6) gradient based on intensity
        const t = dataArray[i] / 255;
        const r = Math.round(8   + (20  - 8)   * t);
        const g = Math.round(145 + (184 - 145)  * t);
        const b = Math.round(178 + (166 - 178)  * t);
        ctx.fillStyle = `rgba(${r},${g},${b},${0.55 + t * 0.45})`;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 1;
      }
    };

    draw();
    return () => cancelAnimationFrame(animationId);
  }, [analyser, status]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-24 bg-slate-100 rounded-xl border border-slate-200"
      aria-hidden="true"
    />
  );
}
