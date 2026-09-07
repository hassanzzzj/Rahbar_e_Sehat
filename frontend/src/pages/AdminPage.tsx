import { useEffect, useState } from "react";

import { Card } from "@/components/ui/Card";
import { SkeletonPage } from "@/components/common/SkeletonPage";
import { api, ApiClientError } from "@/lib/api-client";
import type { AdminStats } from "@/types/api";

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await api.get<AdminStats>("/admin/stats");
        if (!cancelled && res.data) setStats(res.data);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiClientError
              ? err.message
              : "Unable to load system stats.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <SkeletonPage />;

  return (
    <section className="mx-auto max-w-5xl px-3 py-6">
      <header>
        <span className="label-uppercase text-accent-600">Internal</span>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-neutral-900">
          Admin dashboard
        </h1>
        <p className="mt-1 text-sm text-neutral-600">
          Clinical review of anonymized triage decisions, facility stock
          signals, and drift metrics. Requires RBAC-authorized access.
        </p>
      </header>

      {error && (
        <p role="alert" className="mt-3 text-sm text-semantic-emergency">
          {error}
        </p>
      )}

      <div className="mt-4 grid grid-cols-1 gap-2 md:grid-cols-4">
        <Card title="Triage volume (total)">
          <p className="text-3xl font-semibold tracking-tight text-neutral-900">
            {stats?.total_sessions ?? "—"}
          </p>
          <p className="text-xs text-neutral-500">
            Total triage sessions processed.
          </p>
        </Card>
        <Card title="Emergency cases">
          <p className="text-3xl font-semibold tracking-tight text-neutral-900">
            {stats?.emergency_cases ?? "—"}
          </p>
          <p className="text-xs text-neutral-500">
            Sessions flagged EMERGENCY by the deterministic safety layer.
          </p>
        </Card>
        <Card title="Avg response time">
          <p className="text-3xl font-semibold tracking-tight text-neutral-900">
            {stats?.average_response_time_ms
              ? `${stats.average_response_time_ms}ms`
              : "—"}
          </p>
          <p className="text-xs text-neutral-500">
            Mean time from submission to triage response.
          </p>
        </Card>
        <Card title="Active agents">
          <p className="text-3xl font-semibold tracking-tight text-neutral-900">
            {stats?.active_agents ?? "—"}
          </p>
          <p className="text-xs text-neutral-500">
            Agents currently running in the pipeline.
          </p>
        </Card>
      </div>

      <Card title="Recent sessions" className="mt-4">
        <p className="text-sm text-neutral-500">
          No sessions recorded yet.
        </p>
      </Card>
    </section>
  );
}
