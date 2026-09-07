import { useState } from "react";
import { NavLink } from "react-router-dom";
import { Activity, Menu, X, Phone } from "lucide-react";

const NAV_ITEMS = [
  { to: "/", label: "Home", end: true },
  { to: "/triage", label: "Triage", end: false },
  { to: "/facilities", label: "Facilities", end: false },
  { to: "/admin", label: "Admin", end: false },
];

export function SiteHeader() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-[#E5E1DA] bg-white/95 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        {/* Logo */}
        <NavLink
          to="/"
          className="flex items-center gap-2 rounded-lg p-1 transition-opacity hover:opacity-80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#357A53] focus-visible:ring-offset-2"
          aria-label="Rahbar-e-Sehat — Home"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#357A53]">
            <Activity className="h-4 w-4 text-white" aria-hidden="true" />
          </div>
          <div className="hidden sm:block">
            <span className="block text-sm font-bold tracking-tight text-[#1A1815]">
              Rahbar-e-Sehat
            </span>
            <span className="block text-xs text-[#66605A] urdu leading-tight" dir="rtl" lang="ur">
              رہبرِ صحت
            </span>
          </div>
          <span className="block text-sm font-bold tracking-tight text-[#1A1815] sm:hidden">
            رہبر
          </span>
        </NavLink>

        {/* Desktop nav */}
        <nav aria-label="Primary navigation" className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                [
                  "rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-120",
                  isActive
                    ? "bg-[#EEF4F0] text-[#276142] font-semibold"
                    : "text-[#66605A] hover:bg-[#F2F0EC] hover:text-[#333028]",
                ].join(" ")
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Emergency CTA + mobile toggle */}
        <div className="flex items-center gap-2">
          <a
            href="tel:1122"
            className="hidden sm:inline-flex items-center gap-1.5 rounded-lg bg-[#B52D24] px-3 py-2 text-xs font-semibold text-white transition-colors hover:bg-[#8F231C] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#B52D24] focus-visible:ring-offset-2"
            aria-label="Call emergency number 1122"
          >
            <Phone size={13} aria-hidden="true" />
            Emergency? 1122
          </a>

          {/* Mobile menu button */}
          <button
            type="button"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#E5E1DA] text-[#66605A] transition-colors hover:bg-[#F2F0EC] md:hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#357A53]"
            onClick={() => setMobileOpen((o) => !o)}
            aria-expanded={mobileOpen}
            aria-label={mobileOpen ? "Close navigation menu" : "Open navigation menu"}
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {/* Mobile dropdown */}
      {mobileOpen && (
        <nav
          aria-label="Mobile navigation"
          className="border-t border-[#E5E1DA] bg-white px-4 pb-4 pt-2 md:hidden animate-fade-in"
        >
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                [
                  "flex rounded-lg px-3 py-3 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-[#EEF4F0] text-[#276142] font-semibold"
                    : "text-[#66605A] hover:bg-[#F2F0EC] hover:text-[#333028]",
                ].join(" ")
              }
            >
              {item.label}
            </NavLink>
          ))}
          <div className="mt-3 border-t border-[#E5E1DA] pt-3">
            <a
              href="tel:1122"
              onClick={() => setMobileOpen(false)}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#B52D24] px-4 py-3 text-sm font-semibold text-white hover:bg-[#8F231C]"
            >
              <Phone size={15} aria-hidden="true" />
              Call Emergency — 1122
            </a>
          </div>
        </nav>
      )}
    </header>
  );
}
