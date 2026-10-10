import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ErrorBanner } from "../components/ErrorBanner";
import { Skeleton } from "../components/Skeleton";
import { StatusBadge } from "../components/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import { formatDate } from "../lib/format";
import { api } from "../services/api";

export function OverviewPage() {
  const { data, error, loading, reload } = useAsync(() => api.dashboard(), []);

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-28" />
        ))}
      </div>
    );
  }
  if (error) return <ErrorBanner message={error} onRetry={reload} />;
  if (!data) return null;

  const cards = [
    ["Advertisements analyzed", data.total_advertisements],
    ["Potentially suspicious", data.potentially_suspicious],
    ["High / critical risk", data.high_risk],
    ["Detected relationships", data.relationship_count],
  ];
  const chart = Object.entries(data.risk_distribution).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Overview</h1>
        <p className="mt-1 text-sm text-mute">
          Metrics are computed from the local database. {data.seed_advertisement_count} records are synthetic demonstration advertisements.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        {cards.map(([label, value]) => (
          <div key={label} className="rounded-lg border border-line bg-panel p-4">
            <p className="text-xs uppercase tracking-wide text-mute">{label}</p>
            <p className="mt-3 text-3xl font-semibold">{value}</p>
          </div>
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-5">
        <section className="rounded-lg border border-line bg-panel p-4 lg:col-span-2">
          <h2 className="text-sm font-medium">Risk distribution</h2>
          <div className="mt-4 h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chart}>
                <CartesianGrid stroke="#1E232C" vertical={false} />
                <XAxis dataKey="name" stroke="#8B929E" fontSize={11} />
                <YAxis stroke="#8B929E" fontSize={11} allowDecimals={false} />
                <Tooltip contentStyle={{ background: "#111318", border: "1px solid #1E232C" }} />
                <Bar dataKey="value" fill="#3EE0FF" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
        <section className="rounded-lg border border-line bg-panel p-4 lg:col-span-3">
          <h2 className="text-sm font-medium">Potentially coordinated clusters</h2>
          <div className="mt-4 space-y-2">
            {data.campaign_activity.length === 0 ? (
              <p className="text-sm text-mute">No relationship clusters yet.</p>
            ) : (
              data.campaign_activity.map((campaign) => (
                <Link
                  key={campaign.id}
                  to={`/campaigns/${campaign.id}`}
                  className="flex items-center justify-between rounded border border-line px-3 py-2 text-sm hover:bg-white/5"
                >
                  <span>{campaign.label}</span>
                  <span className="text-mute">{campaign.member_count} ads · max {campaign.max_risk_score}</span>
                </Link>
              ))
            )}
          </div>
        </section>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-lg border border-line bg-panel p-4">
          <h2 className="text-sm font-medium">Recent analyses</h2>
          <div className="mt-3 divide-y divide-line">
            {data.recent_advertisements.map((ad) => (
              <Link key={ad.id} to={`/investigations/${ad.id}`} className="block py-3 hover:bg-white/5">
                <div className="flex items-center justify-between gap-3">
                  <p className="line-clamp-2 text-sm">{ad.text}</p>
                  <StatusBadge value={ad.risk_category} />
                </div>
                <p className="mt-1 text-[11px] text-mute">
                  {formatDate(ad.created_at)} {ad.is_seed ? "· synthetic seed" : "· investigator submission"}
                </p>
              </Link>
            ))}
          </div>
        </section>
        <section className="rounded-lg border border-line bg-panel p-4">
          <h2 className="text-sm font-medium">Recent alerts</h2>
          <div className="mt-3 divide-y divide-line">
            {data.recent_alerts.map((alert) => (
              <Link
                key={alert.id}
                to={alert.advertisement_id ? `/investigations/${alert.advertisement_id}` : "/alerts"}
                className="block py-3 hover:bg-white/5"
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm">{alert.alert_type.replaceAll("_", " ")}</p>
                  <StatusBadge value={alert.severity} />
                </div>
                <p className="mt-1 text-[12px] text-mute">{alert.reason}</p>
              </Link>
            ))}
          </div>
        </section>
      </div>
      <p className="text-xs leading-relaxed text-mute">
        FIN-SHIELD provides preliminary risk indicators to support investigation. Its scores and relationships are not proof of fraud. All findings require human review.
      </p>
    </div>
  );
}
