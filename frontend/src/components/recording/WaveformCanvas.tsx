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

             // Clear canvas
             ctx.fillStyle = "rgb(248, 250, 252)"; // bg-slate-50
             ctx.fillRect(0, 0, canvas.width, canvas.height);

             const barWidth = (canvas.width / bufferLength) * 2.5;
             let x = 0;

             for (let i = 0; i < bufferLength; i++) {
                 const barHeight = dataArray[i] / 2; // scale amplitude
                 ctx.fillStyle = "rgb(37, 99, 235)"; // bg-blue-600
                 ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
                 x += barWidth + 1;
             }
        };

        draw();

        return () => {
             cancelAnimationFrame(animationId);
        };
    }, [analyser, status]);

    return (
        <canvas ref={canvasRef} className="w-full h-24 bg-slate-50 border rounded-lg" />
    )
}
