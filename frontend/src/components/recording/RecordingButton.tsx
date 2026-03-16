import { useState, useEffect } from "react";
import { useRecorder } from "../../hooks/useRecorder";
import WaveformCanvas from "./WaveformCanvas";


interface RecordingButtonProps {
    onRecordingComplete?: (blob: Blob) => void;
    onConsentGiven?: (timestamp: string) => void;
}

export default function RecordingButton({ onRecordingComplete, onConsentGiven }: RecordingButtonProps) {
    const { status, startRecording, stopRecording, analyser, blob } = useRecorder();
    const [seconds, setSeconds] = useState(0);
    const [showConsent, setShowConsent] = useState(false);

    // Timer controller hook triggers
    useEffect(() => {
        if (status !== "recording") {
            if (status === "idle") setSeconds(0);
            return;
        }

        const interval = setInterval(() => {
            setSeconds((s) => s + 1);
        }, 1000);

        return () => clearInterval(interval);
    }, [status]);

    // Lift Blob to upper controller boundings
    useEffect(() => {
         if (status === "stopped" && blob && onRecordingComplete) {
              onRecordingComplete(blob);
         }
    }, [status, blob, onRecordingComplete]);

    const formatTime = (totalSecs: number) => {
        const mins = Math.floor(totalSecs / 60);
        const secs = totalSecs % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const handleStartWithConsent = () => {
         // Raise simple modal consent overlay frame triggers
         setShowConsent(true);
    };

    const confirmConsent = () => {
         setShowConsent(false);
         if (onConsentGiven) onConsentGiven(new Date().toISOString());
         startRecording();
    }

    return (
        <div className="flex flex-col gap-4 p-4 border rounded-xl bg-white shadow-sm">
            {/* Consent Modal Overlay (Naive react render) */}
            {showConsent && (
                 <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
                     <div className="p-6 bg-white rounded-lg shadow-xl max-w-sm">
                          <h3 className="text-lg font-bold">Informed Consent</h3>
                          <p className="text-sm text-slate-600 mt-2">I understand this visit will be recorded for transcription and medical summary generation purposes.</p>
                          <div className="flex gap-2 justify-end mt-6">
                               <button onClick={() => setShowConsent(false)} className="px-3 py-1 bg-slate-200 rounded">Cancel</button>
                               <button onClick={confirmConsent} className="px-3 py-1 bg-blue-600 text-white rounded">I Consent</button>
                          </div>
                     </div>
                 </div>
            )}

            <div className="text-center text-2xl font-mono text-slate-800">
                {formatTime(seconds)}
            </div>
            
            <WaveformCanvas analyser={analyser} status={status} />

            <div className="flex justify-center gap-2">
                {status === "idle" && (
                    <button onClick={handleStartWithConsent} className="px-4 py-2 bg-red-600 text-white rounded-lg font-bold hover:bg-red-700 transition">Record</button>
                )}
                {status === "recording" && (
                    <button onClick={stopRecording} className="px-4 py-2 bg-slate-800 text-white rounded-lg font-bold hover:bg-slate-900 transition">Stop</button>
                )}
                {status === "stopped" && (
                     <p className="text-sm text-green-600 mt-2">Recording saved successfully!</p>
                )}
            </div>
        </div>
    )
}
