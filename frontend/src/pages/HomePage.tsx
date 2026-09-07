import { Link } from "react-router-dom";
import {
  MapPin,
  Shield,
  Activity,
  ChevronRight,
  Mic,
  Search,
  Navigation,
} from "lucide-react";

import { Button } from "@/components/ui/Button";

/* ── Feature cards ─────────────────────────────────────────── */
const FEATURES = [
  {
    icon: Mic,
    title: "Urdu Voice & Text",
    body: "Speak or type in Urdu, Roman Urdu, or English. Our AI understands all three — no literacy required.",
    color: "#357A53",
    bg: "#EEF4F0",
  },
  {
    icon: Shield,
    title: "Deterministic Safety",
    body: "A rule-based engine — not AI guesswork — detects emergencies instantly and routes you to care in seconds.",
    color: "#B52D24",
    bg: "#FDF2F1",
  },
  {
    icon: MapPin,
    title: "Nearest Facility",
    body: "Matched to the closest BHU, RHC, THQ, DHQ, or emergency centre that has what you actually need.",
    color: "#C47A18",
    bg: "#FDF8EE",
  },
  {
    icon: Activity,
    title: "Transparent Reasoning",
    body: "Every recommendation shows the clinical protocol it's based on — no black boxes.",
    color: "#66605A",
    bg: "#F9F8F6",
  },
];

/* ── How it works steps ────────────────────────────────────── */
const STEPS = [
  {
    num: "01",
    icon: Mic,
    title: "Describe your symptoms",
    body: "Voice note or typed message — Urdu or English, any spelling.",
  },
  {
    num: "02",
    icon: Activity,
    title: "AI analyses urgency",
    body: "Safety check + clinical protocol retrieval in under 5 seconds.",
  },
  {
    num: "03",
    icon: Navigation,
    title: "Go to the right place",
    body: "Name, address, distance, and phone number of your nearest facility.",
  },
];

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* ── Hero ──────────────────────────────────────────────── */}
      <section className="bg-gradient-to-b from-[#EEF4F0] to-[#F9F8F6] border-b border-[#E5E1DA]">
        <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6 sm:py-16 lg:py-20">
          <div className="max-w-2xl">
            {/* Eyebrow */}
            <span className="inline-flex items-center gap-1.5 rounded-full border border-[#B0D2BC] bg-[#D7E9DC] px-3 py-1 text-xs font-semibold uppercase tracking-wide text-[#276142]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#357A53]" />
              Healthcare Triage &amp; Referral · Pakistan
            </span>

            {/* Main headline */}
            <h1 className="mt-4 text-3xl font-bold tracking-tight text-[#1A1815] sm:text-4xl lg:text-5xl">
              Har Bemaar Ka{" "}
              <span className="text-[#357A53]">Sahi Rasta</span>
            </h1>

            {/* Urdu headline */}
            <p
              className="urdu mt-2 text-xl text-[#66605A]"
              dir="rtl"
              lang="ur"
            >
              ہر بیمار کا صحی راستہ
            </p>

            {/* Sub-copy */}
            <p className="mt-4 text-base leading-relaxed text-[#4D4842] sm:text-lg">
              Describe your symptoms in Urdu — voice or text — and we'll guide
              you to the right level of care, at the right facility, at the
              right time. No app install. No registration.
            </p>

            {/* CTAs */}
            <div className="mt-6 flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link to="/triage">
                  Start Triage
                  <ChevronRight size={18} aria-hidden="true" />
                </Link>
              </Button>
              <Button asChild variant="secondary" size="lg">
                <Link to="/facilities">
                  <Search size={16} aria-hidden="true" />
                  Find a Facility
                </Link>
              </Button>
            </div>

            {/* Disclaimer */}
            <p className="mt-4 text-xs text-[#A8A098]">
              ⚠️ Not a diagnostic tool. For emergencies, call{" "}
              <a href="tel:1122" className="font-bold text-[#B52D24] underline">
                1122
              </a>{" "}
              immediately.
            </p>
          </div>
        </div>
      </section>

      {/* ── How it works ──────────────────────────────────────── */}
      <section className="bg-white border-b border-[#E5E1DA]">
        <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 sm:py-14">
          <div className="mb-8 text-center">
            <span className="label-uppercase text-[#357A53]">How it works</span>
            <h2 className="mt-1 text-2xl font-bold tracking-tight text-[#1A1815]">
              Three steps to the right care
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
            {STEPS.map((step, i) => {
              const Icon = step.icon;
              return (
                <div key={step.num} className="relative flex flex-col items-center text-center">
                  {/* Connector line (desktop) */}
                  {i < STEPS.length - 1 && (
                    <div
                      className="absolute left-[calc(50%+2rem)] top-7 hidden h-0.5 bg-[#D7E9DC] sm:block"
                      style={{ width: "calc(100% - 4rem)" }}
                      aria-hidden="true"
                    />
                  )}

                  {/* Step circle */}
                  <div className="relative flex h-14 w-14 items-center justify-center rounded-full bg-[#EEF4F0] ring-4 ring-white">
                    <Icon size={24} className="text-[#357A53]" aria-hidden="true" />
                    <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-[#357A53] text-[10px] font-bold text-white">
                      {step.num.slice(-1)}
                    </span>
                  </div>

                  <h3 className="mt-3 text-sm font-semibold text-[#1A1815]">{step.title}</h3>
                  <p className="mt-1 text-xs leading-relaxed text-[#66605A]">{step.body}</p>
                </div>
              );
            })}
          </div>

          {/* Bottom CTA */}
          <div className="mt-8 flex justify-center">
            <Button asChild size="md">
              <Link to="/triage">
                <Mic size={16} aria-hidden="true" />
                Begin your triage now
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* ── Feature cards ──────────────────────────────────────── */}
      <section className="bg-[#F9F8F6]">
        <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 sm:py-14">
          <div className="mb-8 text-center">
            <span className="label-uppercase text-[#357A53]">System capabilities</span>
            <h2 className="mt-1 text-2xl font-bold tracking-tight text-[#1A1815]">
              Built for Pakistan's healthcare reality
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {FEATURES.map(({ icon: Icon, title, body, color, bg }) => (
              <div
                key={title}
                className="flex gap-4 rounded-xl border border-[#E5E1DA] bg-white p-5 transition-shadow duration-200 hover:shadow-[0_4px_12px_0_rgba(0,0,0,0.08)]"
              >
                <div
                  className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl"
                  style={{ backgroundColor: bg }}
                >
                  <Icon size={22} style={{ color }} aria-hidden="true" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-[#1A1815]">{title}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-[#66605A]">{body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Emergency banner ───────────────────────────────────── */}
      <section className="bg-[#FDF2F1] border-t border-[#F4C1BE]">
        <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
          <div className="flex flex-col items-center justify-between gap-3 text-center sm:flex-row sm:text-left">
            <div>
              <p className="text-sm font-semibold text-[#B52D24]">
                ⚠️ If you think this is an emergency — don't wait.
              </p>
              <p className="text-sm text-[#66605A]">
                Call{" "}
                <a href="tel:1122" className="font-semibold text-[#B52D24] underline">
                  1122
                </a>{" "}
                (Rescue) or{" "}
                <a href="tel:115" className="font-semibold text-[#B52D24] underline">
                  115
                </a>{" "}
                (Edhi Ambulance) immediately.
              </p>
            </div>
            <Button asChild variant="danger" size="md">
              <Link to="/triage">
                Emergency Triage
                <ChevronRight size={16} aria-hidden="true" />
              </Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}
