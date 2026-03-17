import { useState, useEffect } from "react";
import { useRecorder } from "../../hooks/useRecorder";
import WaveformCanvas from "./WaveformCanvas";
import { Mic, Square, CheckCircle2, ShieldAlert } from "lucide-react";

interface RecordingButtonProps {
  onRecordingComplete?: (blob: Blob) => void;
  onConsentGiven?: (timestamp: string) => void;
}

export default function RecordingButton({ onRecordingComplete, onConsentGiven }: RecordingButtonProps) {
  const { status, startRecording, stopRecording, analyser, blob } = useRecorder();
  const [seconds, setSeconds]       = useState(0);
  const [showConsent, setShowConsent] = useState(false);

  useEffect(() => {
    if (status !== "recording") {
      if (status === "idle") setSeconds(0);
      return;
    }
    const id = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [status]);

  useEffect(() => {
    if (status === "stopped" && blob && onRecordingComplete) {
      onRecordingComplete(blob);
    }
  }, [status, blob, onRecordingComplete]);

  const formatTime = (s: number) =>
    `${Math.floor(s / 60).toString().padStart(2, "0")}:${(s % 60).toString().padStart(2, "0")}`;

  const confirmConsent = () => {
    setShowConsent(false);
    if (onConsentGiven) onConsentGiven(new Date().toISOString());
    startRecording();
  };

  return (
    <>
      {/* ── Consent Modal ── */}
      {showConsent && (
        <div
          className="fixed inset-0 flex items-center justify-center z-50"
          style={{ background: "rgba(15,23,42,0.55)" }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="consent-title"
          aria-describedby="consent-desc"
        >
          <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full mx-4 overflow-hidden">
            <div className="p-5 border-b border-slate-100">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center flex-shrink-0" aria-hidden="true">
                  <ShieldAlert className="w-5 h-5 text-amber-500" />
                </div>
                <div>
                  <h3 id="consent-title" className="font-heading font-semibold text-slate-900 text-base">
                    Informed Consent Required
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">Please read before proceeding</p>
                </div>
              </div>
            </div>
            <div className="p-5">
              <p id="consent-desc" className="text-sm text-slate-600 leading-relaxed">
                By proceeding, you confirm that the patient has been informed and consents to this
                visit being recorded for transcription and medical summary generation purposes.
              </p>
            </div>
            <div className="px-5 pb-5 flex gap-3 justify-end">
              <button
                onClick={() => setShowConsent(false)}
                className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors duration-150 cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={confirmConsent}
                className="px-4 py-2 text-sm font-semibold text-white bg-cyan-600 rounded-lg hover:bg-cyan-700 transition-colors duration-150 cursor-pointer"
              >
                I Consent — Start Recording
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Recording card ── */}
      <div className="flex flex-col gap-5 p-5 border border-slate-100 rounded-2xl bg-slate-50">

        {/* Timer */}
        <div className="flex items-center justify-center gap-3">
          {status === "recording" && (
            <span
              className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse flex-shrink-0"
              aria-label="Recording active"
            />
          )}
          <span
            className="text-4xl font-mono font-bold text-slate-800 tracking-widest tabular-nums"
            aria-live="polite"
            aria-label={`Timer: ${formatTime(seconds)}`}
          >
            {formatTime(seconds)}
          </span>
        </div>

        {/* Waveform */}
        <WaveformCanvas analyser={analyser} status={status} />

        {/* Controls */}
        <div className="flex justify-center">
          {status === "idle" && (
            <button
              onClick={() => setShowConsent(true)}
              className="inline-flex items-center gap-2 px-7 py-3 bg-red-500 text-white font-semibold text-sm rounded-xl hover:bg-red-600 transition-colors duration-150 cursor-pointer shadow-lg shadow-red-200 min-h-[44px]"
              aria-label="Start recording"
            >
              <Mic className="w-4 h-4" aria-hidden="true" />
              Start Recording
            </button>
          )}
          {status === "recording" && (
            <button
              onClick={stopRecording}
              className="inline-flex items-center gap-2 px-7 py-3 bg-slate-800 text-white font-semibold text-sm rounded-xl hover:bg-slate-900 transition-colors duration-150 cursor-pointer min-h-[44px]"
              aria-label="Stop recording"
            >
              <Square className="w-4 h-4 fill-current" aria-hidden="true" />
              Stop Recording
            </button>
          )}
          {status === "stopped" && (
            <div
              className="inline-flex items-center gap-2 px-5 py-3 bg-emerald-50 text-emerald-700 rounded-xl border border-emerald-100"
              role="status"
              aria-live="polite"
            >
              <CheckCircle2 className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
              <span className="text-sm font-semibold">Recording complete — uploading…</span>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
