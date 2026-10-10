import { Link } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";
import { Skeleton } from "../components/Skeleton";
import { StatusBadge } from "../components/StatusBadge";
import { useToast } from "../components/Toast";
import { useAsync } from "../hooks/useAsync";
import { formatDate } from "../lib/format";
import { api } from "../services/api";
import { ApiError } from "../types/api";

export function AlertsPage() {
  const toast = useToast();
  const { data, error, loading, reload, setData } = useAsync(() => api.alerts(), []);

  async function markRead(id: string) {
    try {
      const updated = await api.markAlert(id, true);
      setData((current) => current?.map((item) => (item.id === id ? updated : item)) ?? null);
      toast("Alert marked as read.");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Could not update alert.", "err");
    }
  }

  if (loading) return <Skeleton className="h-80" />;
  if (error) return <ErrorBanner message={error} onRetry={reload} />;
  if (!data?.length) {
    return <EmptyState title="No alerts" body="Alerts are created when analysis rules fire, not when this page refreshes." />;
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Alerts</h1>
        <p className="mt-1 text-sm text-mute">Stored rule hits. Duplicate creation is suppressed with idempotency keys.</p>
      </div>
      <ul className="space-y-3">
        {data.map((alert) => (
          <li key={alert.id} className="rounded-lg border border-line bg-panel p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <StatusBadge value={alert.severity} />
                <p className="text-sm font-medium">{alert.alert_type.replaceAll("_", " ")}</p>
                {!alert.is_read ? <span className="text-[11px] text-accent">unread</span> : null}
              </div>
              <p className="text-xs text-mute">{formatDate(alert.created_at)}</p>
            </div>
            <p className="mt-2 text-sm text-mute">{alert.reason}</p>
            <div className="mt-3 flex gap-4 text-sm">
              {alert.advertisement_id ? (
                <Link className="text-accent" to={`/investigations/${alert.advertisement_id}`}>
                  Open investigation
                </Link>
              ) : null}
              {alert.campaign_id ? (
                <Link className="text-accent" to={`/campaigns/${alert.campaign_id}`}>
                  Open cluster
                </Link>
              ) : null}
              {!alert.is_read ? (
                <button type="button" className="text-mute underline" onClick={() => void markRead(alert.id)}>
                  Mark read
                </button>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
