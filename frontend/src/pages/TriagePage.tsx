import { useCallback, useState } from "react";
import {
  Send,
  MapPin,
  Phone,
  Pill,
  Volume2,
  WifiOff,
  AlertTriangle,
  ChevronRight,
  RotateCcw,
} from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Textarea } from "@/components/ui/Input";
import { UrgencyBadge } from "@/components/ui/UrgencyBadge";
import { VoiceRecorder } from "@/components/ui/VoiceRecorder";
import { useNetworkStatus } from "@/hooks/useNetworkStatus";
import { API_BASE_URL, api, ApiClientError } from "@/lib/api-client";
import type { APIResponse, TranscribeResponse, TriageResponse } from "@/types/api";

/* ── Progress steps ────────────────────────────────────────── */
type Step = "input" | "analyzing" | "result";
const STEP_LABELS: Record<Step, string> = {
  input: "Describe",
  analyzing: "Analysing",
  result: "Result",
};

function ProgressBar({ step }: { step: Step }) {
  const steps: Step[] = ["input", "analyzing", "result"];
  const current = steps.indexOf(step);
  return (
    <div className="mb-6 flex items-center gap-2" aria-label="Progress">
      {steps.map((s, i) => (
        <div key={s} className="flex items-center gap-2">
          <div
            className={[
              "flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold transition-colors duration-300",
              i <= current
                ? "bg-[#357A53] text-white"
                : "bg-[#E5E1DA] text-[#A8A098]",
            ].join(" ")}
          >
            {i + 1}
          </div>
          <span
            className={[
              "text-xs font-medium",
              i <= current ? "text-[#276142]" : "text-[#A8A098]",
            ].join(" ")}
          >
            {STEP_LABELS[s]}
          </span>
          {i < steps.length - 1 && (
            <ChevronRight size={14} className="text-[#CCC7BC]" aria-hidden="true" />
          )}
        </div>
      ))}
    </div>
  );
}

/* ── Main page ─────────────────────────────────────────────── */
export default function TriagePage() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<TriageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { isOnline } = useNetworkStatus();

  const step: Step = result ? "result" : submitting ? "analyzing" : "input";

  const handleVoiceReady = useCallback(async (blob: Blob) => {
    setError(null);
    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("file", blob, "recording.webm");
      formData.append("language", "ur");

      const res = await fetch(`${API_BASE_URL}/transcribe`, { method: "POST", body: formData });
      const body = (await res.json().catch(() => null)) as APIResponse<TranscribeResponse> | null;
      if (!res.ok || !body?.success) throw new Error("Transcription failed");
      const text = body.data?.text ?? "";
      if (text) setInput((prev) => (prev ? `${prev} ${text}` : text));
    } catch {
      setError("Voice transcription failed. Please type your symptoms instead.");
    } finally {
      setSubmitting(false);
    }
  }, []);

  const handleSubmit = async () => {
    if (submitting || input.trim().length === 0) return;
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.post<TriageResponse>("/triage", {
        patient_message: input.trim(),
      });
      setResult(response.data);
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to reach the triage service. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setInput("");
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#F9F8F6]">
      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
        {/* Offline banner */}
        {!isOnline && (
          <div
            role="alert"
            className="mb-4 flex items-center gap-2 rounded-xl border border-[#F5DFA0] bg-[#FDF8EE] px-4 py-3 text-sm text-[#C47A18] animate-slide-up"
          >
            <WifiOff size={16} className="shrink-0" aria-hidden="true" />
            You are offline. Submissions will be queued when connectivity returns.
          </div>
        )}

        {/* Progress */}
        <ProgressBar step={step} />

        {/* Two-panel layout on desktop */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 lg:gap-6">
          {/* ── Left: Input panel ─────────────────────────────── */}
          <div className="flex flex-col gap-4">
            <Card variant="default">
              <div className="mb-1">
                <h1 className="text-lg font-bold text-[#1A1815]">Describe your symptoms</h1>
                <p className="mt-1 text-xs text-[#66605A]">
                  In your own words — Urdu, Roman Urdu, or English.
                  <strong className="ml-1 text-[#B52D24]">This is not a diagnosis.</strong>
                </p>
              </div>

              {/* Voice recorder */}
              <div className="rounded-xl bg-[#F9F8F6] border border-[#E5E1DA] p-4">
                <VoiceRecorder onAudioReady={handleVoiceReady} disabled={submitting} />
              </div>

              {/* Divider */}
              <div className="flex items-center gap-2 my-1">
                <div className="flex-1 h-px bg-[#E5E1DA]" />
                <span className="text-xs text-[#A8A098] font-medium">or type below</span>
                <div className="flex-1 h-px bg-[#E5E1DA]" />
              </div>

              {/* Symptom textarea */}
              <Textarea
                label="Symptom description"
                hint="مثال: 'دو دن سے بخار اور کھانسی ہے' — or 'fever and cough for two days'"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                maxLength={2000}
                disabled={submitting}
                rows={4}
                placeholder="Type here…"
              />

              {/* Character count */}
              <div className="flex justify-end">
                <span className={`text-xs ${input.length > 1900 ? "text-[#B52D24]" : "text-[#A8A098]"}`}>
                  {input.length}/2000
                </span>
              </div>

              {/* Submit button */}
              <Button
                onClick={handleSubmit}
                disabled={submitting || input.trim().length === 0}
                loading={submitting}
                size="lg"
                className="w-full"
              >
                {submitting ? "Analysing symptoms…" : (
                  <>
                    <Send size={16} aria-hidden="true" />
                    Analyse symptoms
                  </>
                )}
              </Button>

              {result && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleReset}
                  className="w-full mt-1"
                >
                  <RotateCcw size={14} aria-hidden="true" />
                  Start new triage
                </Button>
              )}
            </Card>

            {/* Error */}
            {error && (
              <div
                role="alert"
                className="flex items-start gap-2 rounded-xl border border-[#F4C1BE] bg-[#FDF2F1] px-4 py-3 text-sm text-[#B52D24] animate-slide-up"
              >
                <AlertTriangle size={16} className="shrink-0 mt-0.5" aria-hidden="true" />
                {error}
              </div>
            )}
          </div>

          {/* ── Right: Result panel ───────────────────────────── */}
          <div className="flex flex-col gap-4">
            {/* Placeholder when no result yet */}
            {!result && !submitting && (
              <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-[#D7E9DC] bg-white px-6 py-16 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[#EEF4F0]">
                  <MapPin size={28} className="text-[#357A53]" aria-hidden="true" />
                </div>
                <p className="mt-3 text-sm font-semibold text-[#4D4842]">Your results will appear here</p>
                <p className="mt-1 text-xs text-[#A8A098]">
                  Describe your symptoms and press "Analyse symptoms"
                </p>
              </div>
            )}

            {/* Loading skeleton */}
            {submitting && (
              <div className="flex flex-col gap-3 rounded-xl border border-[#E5E1DA] bg-white p-5 animate-pulse">
                <div className="h-4 w-32 rounded bg-[#E5E1DA]" />
                <div className="h-8 w-24 rounded-full bg-[#E5E1DA]" />
                <div className="space-y-2">
                  <div className="h-3 w-full rounded bg-[#F2F0EC]" />
                  <div className="h-3 w-5/6 rounded bg-[#F2F0EC]" />
                  <div className="h-3 w-4/6 rounded bg-[#F2F0EC]" />
                </div>
                <div className="mt-2 h-20 w-full rounded-xl bg-[#F2F0EC]" />
              </div>
            )}

            {/* Actual result */}
            {result && (
              <div className="flex flex-col gap-4 animate-slide-up">
                {/* Urgency header card */}
                <Card variant={result.is_emergency ? "emergency" : "default"}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-[#66605A]">
                        Triage Result
                      </p>
                      <div className="mt-2">
                        {result.urgency ? (
                          <UrgencyBadge urgency={result.urgency} size="lg" />
                        ) : (
                          <span className="text-sm text-[#A8A098]">Not classified</span>
                        )}
                      </div>
                    </div>
                    <span className="text-xs text-[#A8A098] font-mono">
                      #{result.session_id.slice(0, 8)}
                    </span>
                  </div>

                  {/* Emergency alert */}
                  {result.is_emergency && (
                    <div
                      role="alert"
                      className="mt-3 flex items-start gap-2 rounded-lg border border-[#F4C1BE] bg-[#FDF2F1] p-3"
                    >
                      <AlertTriangle
                        size={16}
                        className="shrink-0 mt-0.5 text-[#B52D24]"
                        aria-hidden="true"
                      />
                      <div>
                        <p className="text-sm font-bold text-[#B52D24]">Emergency detected</p>
                        <p className="text-sm text-[#66605A]">
                          Seek immediate care. Call{" "}
                          <a href="tel:1122" className="font-bold text-[#B52D24] underline">
                            1122
                          </a>{" "}
                          now.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Reasoning trace */}
                  {result.reasoning_trace && (
                    <div className="mt-3 rounded-lg bg-[#F9F8F6] border border-[#E5E1DA] p-3">
                      <p className="text-xs font-semibold uppercase tracking-wide text-[#A8A098] mb-1">
                        Clinical reasoning
                      </p>
                      <p className="text-sm leading-relaxed text-[#4D4842]">
                        {result.reasoning_trace}
                      </p>
                    </div>
                  )}

                  {/* Urdu response */}
                  {result.patient_message_urdu && (
                    <div className="mt-3 rounded-lg border border-[#B0D2BC] bg-[#EEF4F0] p-3">
                      <p className="text-xs font-semibold uppercase tracking-wide text-[#357A53] mb-1">
                        Response in Urdu
                      </p>
                      <p className="urdu text-base text-[#1A1815]" dir="rtl" lang="ur">
                        {result.patient_message_urdu}
                      </p>
                    </div>
                  )}

                  {/* Audio playback */}
                  {result.audio_url && (
                    <div className="mt-3 flex items-center gap-2 rounded-lg border border-[#E5E1DA] bg-[#F9F8F6] p-3">
                      <Volume2 size={16} className="shrink-0 text-[#357A53]" aria-hidden="true" />
                      <audio
                        controls
                        src={result.audio_url}
                        aria-label="Urdu audio response"
                        className="h-8 w-full"
                      />
                    </div>
                  )}
                </Card>

                {/* Recommended facility */}
                {result.recommended_facility && (
                  <Card variant="routine" title="Recommended Facility">
                    <div className="flex items-start gap-3">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#D7E9DC]">
                        <MapPin size={18} className="text-[#357A53]" aria-hidden="true" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-[#1A1815] truncate">
                          {result.recommended_facility.name}
                        </p>
                        <p className="mt-0.5 text-xs text-[#66605A]">
                          {result.recommended_facility.address}
                        </p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          <span className="inline-flex items-center gap-1 rounded-full bg-[#EEF4F0] border border-[#B0D2BC] px-2 py-0.5 text-xs font-medium text-[#276142]">
                            {result.recommended_facility.facility_type}
                          </span>
                          <span className="inline-flex items-center gap-1 rounded-full bg-[#F9F8F6] border border-[#E5E1DA] px-2 py-0.5 text-xs text-[#66605A]">
                            {result.recommended_facility.distance_km.toFixed(1)} km away
                          </span>
                          {result.recommended_facility.emergency_capable && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-[#FDF2F1] border border-[#F4C1BE] px-2 py-0.5 text-xs font-medium text-[#B52D24]">
                              Emergency-capable
                            </span>
                          )}
                        </div>
                        {result.recommended_facility.phone_number && (
                          <a
                            href={`tel:${result.recommended_facility.phone_number}`}
                            className="mt-2 inline-flex items-center gap-1.5 text-sm font-medium text-[#357A53] hover:text-[#276142]"
                          >
                            <Phone size={14} aria-hidden="true" />
                            {result.recommended_facility.phone_number}
                          </a>
                        )}
                      </div>
                    </div>
                  </Card>
                )}

                {/* Medicine availability */}
                {result.medicine_status && (
                  <Card variant="default" title="Medicine Availability">
                    <div className="flex items-center gap-2 mb-2">
                      <Pill size={15} className="text-[#357A53]" aria-hidden="true" />
                      <span className="text-xs text-[#66605A]">At recommended facility</span>
                    </div>
                    {result.medicine_status.medicines_available.length > 0 && (
                      <div className="mb-2">
                        <p className="text-xs font-semibold uppercase tracking-wide text-[#357A53] mb-1">
                          ✓ Available
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {result.medicine_status.medicines_available.map((m) => (
                            <span
                              key={m}
                              className="rounded-full bg-[#EEF4F0] border border-[#B0D2BC] px-2 py-0.5 text-xs text-[#276142]"
                            >
                              {m}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {result.medicine_status.medicines_unavailable.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-[#B52D24] mb-1">
                          ✗ Not available
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {result.medicine_status.medicines_unavailable.map((m) => (
                            <span
                              key={m}
                              className="rounded-full bg-[#FDF2F1] border border-[#F4C1BE] px-2 py-0.5 text-xs text-[#B52D24]"
                            >
                              {m}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </Card>
                )}

                {/* Find more facilities link */}
                <div className="text-center">
                  <Link
                    to="/facilities"
                    className="inline-flex items-center gap-1 text-sm font-medium text-[#357A53] hover:text-[#276142] hover:underline"
                  >
                    See all nearby facilities
                    <ChevronRight size={14} aria-hidden="true" />
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
