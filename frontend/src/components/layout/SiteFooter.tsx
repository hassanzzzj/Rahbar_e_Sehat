import { ShieldCheck, AlertCircle, Clock } from "lucide-react";

const TRUST_BADGES = [
  {
    icon: ShieldCheck,
    label: "Not a diagnostic tool",
    desc: "Triage & referral only",
  },
  {
    icon: AlertCircle,
    label: "Emergency? Call 1122",
    desc: "Pakistan emergency services",
  },
  {
    icon: Clock,
    label: "24/7 Available",
    desc: "Any time, any place",
  },
];

export function SiteFooter() {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-[#E5E1DA] bg-[#F2F0EC]">
      {/* Trust badges */}
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {TRUST_BADGES.map(({ icon: Icon, label, desc }) => (
            <div key={label} className="flex items-start gap-3">
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#D7E9DC]">
                <Icon size={16} className="text-[#276142]" aria-hidden="true" />
              </div>
              <div>
                {label === "Emergency? Call 1122" ? (
                  <a href="tel:1122" className="text-xs font-semibold text-[#333028] underline hover:text-[#276142]">
                    {label}
                  </a>
                ) : (
                  <p className="text-xs font-semibold text-[#333028]">{label}</p>
                )}
                <p className="text-xs text-[#66605A]">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-[#D9D5CE] bg-[#E5E1DA]/60">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-4 py-3 sm:flex-row sm:px-6">
          <p className="text-xs text-[#66605A]">
            &copy; {year} Rahbar-e-Sehat &mdash;{" "}
            <span className="urdu text-sm" dir="rtl" lang="ur">
              ہر بیمار کا صحی راستہ
            </span>
          </p>
          <p className="text-xs font-medium uppercase tracking-wide text-[#A8A098]">
            AI-assisted triage · Not a substitute for medical advice
          </p>
        </div>
      </div>
    </footer>
  );
}
