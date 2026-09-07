import { useEffect, useState } from "react";
import { WifiOff } from "lucide-react";

export function OfflineBanner() {
  const [offline, setOffline] = useState<boolean>(
    typeof navigator !== "undefined" && !navigator.onLine,
  );

  useEffect(() => {
    const handleOffline = () => setOffline(true);
    const handleOnline = () => setOffline(false);
    window.addEventListener("offline", handleOffline);
    window.addEventListener("online", handleOnline);
    return () => {
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("online", handleOnline);
    };
  }, []);

  if (!offline) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center justify-center gap-1 bg-accent-600 px-2 py-1 text-sm font-medium text-white"
    >
      <WifiOff className="h-[2] w-[2]" aria-hidden="true" />
      <span>You are offline. Requests will retry when your connection returns.</span>
    </div>
  );
}
