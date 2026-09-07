import { useEffect, useRef, useState } from "react";
import { Mic, Square, MicOff } from "lucide-react";

import { useVoiceRecorder } from "@/hooks/useVoiceRecorder";

interface VoiceRecorderProps {
  onAudioReady: (blob: Blob) => void;
  disabled?: boolean;
}

export function VoiceRecorder({ onAudioReady, disabled }: VoiceRecorderProps) {
  const { isRecording, startRecording, stopRecording, audioBlob, error, isSupported } =
    useVoiceRecorder();
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (isRecording) {
      setElapsed(0);
      timerRef.current = setInterval(() => setElapsed((s) => s + 1), 1000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRecording]);

  useEffect(() => {
    if (audioBlob) onAudioReady(audioBlob);
  }, [audioBlob, onAudioReady]);

  const formatTime = (s: number) =>
    `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

  if (!isSupported) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-[#E5E1DA] bg-[#F9F8F6] p-4 text-sm text-[#66605A]">
        <MicOff size={16} className="shrink-0" aria-hidden="true" />
        Voice recording is not supported in this browser. Please type your symptoms below.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {/* Voice button + timer */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={isRecording ? stopRecording : startRecording}
          disabled={disabled}
          aria-label={isRecording ? "Stop recording" : "Start voice recording in Urdu"}
          className={[
            "relative flex h-14 w-14 shrink-0 items-center justify-center rounded-full border-2 transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
            "disabled:opacity-40 disabled:cursor-not-allowed",
            isRecording
              ? "border-[#B52D24] bg-[#FDF2F1] text-[#B52D24] focus-visible:ring-[#B52D24] emergency-pulse"
              : "border-[#357A53] bg-[#EEF4F0] text-[#357A53] hover:bg-[#D7E9DC] focus-visible:ring-[#357A53]",
          ].join(" ")}
        >
          {isRecording ? (
            <Square size={22} aria-hidden="true" />
          ) : (
            <Mic size={22} aria-hidden="true" />
          )}
        </button>

        <div className="flex flex-col">
          {isRecording ? (
            <>
              <div className="flex items-center gap-2">
                <span
                  className="inline-block h-2 w-2 rounded-full bg-[#B52D24]"
                  style={{ animation: "pulseDot 1.4s ease-in-out infinite" }}
                />
                <span className="text-sm font-semibold text-[#B52D24]">Recording…</span>
                <span className="font-mono text-sm tabular-nums text-[#66605A]">
                  {formatTime(elapsed)}
                </span>
              </div>
              <p className="mt-0.5 text-xs text-[#A8A098]">Tap the button to stop</p>
            </>
          ) : (
            <>
              <span className="text-sm font-semibold text-[#333028]">Voice input</span>
              <p className="mt-0.5 text-xs text-[#A8A098]">
                Speak in Urdu — بولیں اپنی تکلیف
              </p>
            </>
          )}
        </div>
      </div>

      {error && (
        <p role="alert" className="text-xs text-[#B52D24]">
          {error}
        </p>
      )}
    </div>
  );
}
