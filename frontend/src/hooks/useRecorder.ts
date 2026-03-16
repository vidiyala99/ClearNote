import { useState, useRef, useCallback } from "react";

export type RecorderStatus = "idle" | "recording" | "paused" | "stopped";

export const useRecorder = () => {
  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [blob, setBlob] = useState<Blob | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Setup Web Audio API for Waveform
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const audioCtx = new AudioContextClass();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      
      audioContextRef.current = audioCtx;
      analyserRef.current = analyser;

      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        setBlob(audioBlob);
        setStatus("stopped");
        
        // Clean up tracks
        stream.getTracks().forEach(track => track.stop());
        if (audioContextRef.current) {
             audioContextRef.current.close();
        }
      };

      recorder.start();
      setStatus("recording");
    } catch (err) {
      console.error("Failed to start recording:", err);
      setStatus("idle");
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && (status === "recording" || status === "paused")) {
      mediaRecorderRef.current.stop();
    }
  }, [status]);

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && status === "recording") {
      mediaRecorderRef.current.pause();
      setStatus("paused");
    }
  }, [status]);

  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && status === "paused") {
      mediaRecorderRef.current.resume();
      setStatus("recording");
    }
  }, [status]);

  return {
    status,
    blob,
    analyser: analyserRef.current,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
  };
}
