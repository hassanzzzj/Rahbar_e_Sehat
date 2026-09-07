import { AlertTriangle, Clock, CheckCircle, Heart } from "lucide-react";

type Urgency = "EMERGENCY" | "URGENT" | "ROUTINE" | "SELF_CARE";

interface Props {
  urgency: Urgency;
  size?: "sm" | "md" | "lg";
}

const CONFIG: Record<
  Urgency,
  { label: string; icon: typeof AlertTriangle; bg: string; text: string; border: string; pulse: boolean }
> = {
  EMERGENCY: {
    label: "Emergency",
    icon: AlertTriangle,
    bg: "#FDF2F1",
    text: "#B52D24",
    border: "#F4C1BE",
    pulse: true,
  },
  URGENT: {
    label: "Urgent",
    icon: Clock,
    bg: "#FDF8EE",
    text: "#C47A18",
    border: "#F5DFA0",
    pulse: false,
  },
  ROUTINE: {
    label: "Routine",
    icon: CheckCircle,
    bg: "#EEF4F0",
    text: "#357A53",
    border: "#B0D2BC",
    pulse: false,
  },
  SELF_CARE: {
    label: "Self-care",
    icon: Heart,
    bg: "#F9F8F6",
    text: "#66605A",
    border: "#E5E1DA",
    pulse: false,
  },
};

const SIZE_CLASSES = {
  sm: "text-xs px-2 py-0.5 gap-1",
  md: "text-sm px-3 py-1 gap-1.5",
  lg: "text-base px-4 py-1.5 gap-2",
};

const ICON_SIZE = { sm: 12, md: 14, lg: 16 };

export function UrgencyBadge({ urgency, size = "md" }: Props) {
  const cfg = CONFIG[urgency];
  const Icon = cfg.icon;

  return (
    <span
      className={`inline-flex items-center font-semibold rounded-full border ${SIZE_CLASSES[size]} ${
        cfg.pulse ? "emergency-pulse" : ""
      }`}
      style={{
        backgroundColor: cfg.bg,
        color: cfg.text,
        borderColor: cfg.border,
      }}
      role="status"
      aria-label={`Urgency: ${cfg.label}`}
    >
      <Icon size={ICON_SIZE[size]} aria-hidden="true" />
      {cfg.label}
    </span>
  );
}
