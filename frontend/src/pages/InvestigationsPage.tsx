import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";
import { Skeleton } from "../components/Skeleton";
import { StatusBadge } from "../components/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import { formatDate } from "../lib/format";
import { api } from "../services/api";

export function InvestigationsPage() {
  const [q, setQ] = useState("");
  const [risk, setRisk] = useState("");
  const [page, setPage] = useState(1);
  const params = useMemo(() => ({ q, risk, page, page_size: 12 }), [q, risk, page]);
  const { data, error, loading, reload } = useAsync(() => api.ads(params), [q, risk, page]);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Investigations</h1>
        <p className="mt-1 text-sm text-mute">Search stored analyses. Seeded rows are synthetic demonstration data.</p>
      </div>
      <div className="flex flex-wrap gap-3">
        <input
          className="w-72 rounded border border-line bg-panel px-3 py-2 text-sm outline-none focus:border-accent"
          placeholder="Search advertisement text"
          value={q}
          onChange={(event) => {
            setPage(1);
            setQ(event.target.value);
          }}
        />
        <select
          className="rounded border border-line bg-panel px-3 py-2 text-sm"
          value={risk}
          onChange={(event) => {
            setPage(1);
            setRisk(event.target.value);
          }}
        >
          <option value="">All risk categories</option>
          {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </div>
      {loading ? <Skeleton className="h-64" /> : null}
      {error ? <ErrorBanner message={error} onRetry={reload} /> : null}
      {data && data.items.length === 0 ? (
        <EmptyState title="No advertisements match" body="Adjust filters or analyze a new advertisement." />
      ) : null}
      {data && data.items.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border border-line">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-panel text-[11px] uppercase tracking-wide text-mute">
              <tr>
                <th className="px-3 py-2">Preview</th>
                <th className="px-3 py-2">Risk</th>
                <th className="px-3 py-2">Score</th>
                <th className="px-3 py-2">Entities</th>
                <th className="px-3 py-2">Related</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">When</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((ad) => (
                <tr key={ad.id} className="border-t border-line hover:bg-white/5">
                  <td className="max-w-md px-3 py-3">
                    <Link to={`/investigations/${ad.id}`} className="line-clamp-2 hover:text-accent">
                      {ad.text}
                    </Link>
                    {ad.is_seed ? <p className="mt-1 text-[11px] text-mute">synthetic seed</p> : null}
                  </td>
                  <td className="px-3 py-3">
                    <StatusBadge value={ad.risk_category} />
                  </td>
                  <td className="px-3 py-3">{ad.risk_score}</td>
                  <td className="px-3 py-3">{ad.entity_count}</td>
                  <td className="px-3 py-3">{ad.related_count}</td>
                  <td className="px-3 py-3">{ad.review_status.replace("_", " ")}</td>
                  <td className="px-3 py-3 text-mute">{formatDate(ad.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      {data && data.total > data.page_size ? (
        <div className="flex items-center gap-3 text-sm">
          <button
            className="rounded border border-line px-3 py-1 disabled:opacity-40"
            disabled={page <= 1}
            onClick={() => setPage((value) => value - 1)}
            type="button"
          >
            Previous
          </button>
          <span className="text-mute">
            Page {data.page} of {Math.ceil(data.total / data.page_size)}
          </span>
          <button
            className="rounded border border-line px-3 py-1 disabled:opacity-40"
            disabled={page >= Math.ceil(data.total / data.page_size)}
            onClick={() => setPage((value) => value + 1)}
            type="button"
          >
            Next
          </button>
        </div>
      ) : null}
    </div>
  );
}
