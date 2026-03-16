import { renderHook, act } from "@testing-library/react";
import { useRecorder } from "./useRecorder";
import { vi, describe, it, expect, beforeEach } from "vitest";


describe("useRecorder Hook", () => {
    beforeEach(() => {
        // 1. Mock getUserMedia
        Object.defineProperty(navigator, 'mediaDevices', {
            value: {
                getUserMedia: vi.fn().mockResolvedValue({
                     getTracks: () => [{ stop: vi.fn() }]
                })
            },
            writable: true
        });

        // 2. Mock AudioContext
        const mockAudioContext = vi.fn().mockImplementation(() => ({
             createMediaStreamSource: vi.fn().mockReturnValue({ connect: vi.fn() }),
             createAnalyser: vi.fn().mockReturnValue({ fftSize: 256, frequencyBinCount: 128 }),
             close: vi.fn()
        }));
        (window as any).AudioContext = mockAudioContext;

        // 3. Mock MediaRecorder
        const mockMediaRecorder = vi.fn().mockImplementation(() => ({
             start: vi.fn(),
             stop: vi.fn(),
             pause: vi.fn(),
             resume: vi.fn(),
             ondataavailable: null,
             onstop: null,
             state: "inactive"
        }));
        (window as any).MediaRecorder = mockMediaRecorder;
    });

    it("should initialize with idle status", () => {
         const { result } = renderHook(() => useRecorder());
         expect(result.current.status).toBe("idle");
         expect(result.current.blob).toBeNull();
    });

    it("should transition to recording on startRecording()", async () => {
         const { result } = renderHook(() => useRecorder());
         
         await act(async () => {
              await result.current.startRecording();
         });

         expect(result.current.status).toBe("recording");
    });

    it("should transition to stopped when stopRecording is triggered", async () => {
         const { result } = renderHook(() => useRecorder());
         
         await act(async () => {
              await result.current.startRecording();
         });

         const mockRecorderInstance = (window as any).MediaRecorder.mock.results[0].value;
         
         act(() => {
              result.current.stopRecording();
              
              // Simulate interval stop trigger
              if (mockRecorderInstance.onstop) {
                   mockRecorderInstance.onstop();
              }
         });

         expect(result.current.status).toBe("stopped");
    });
});
