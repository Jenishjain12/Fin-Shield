import { FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ErrorBanner } from "../components/ErrorBanner";
import { Skeleton } from "../components/Skeleton";
import { StatusBadge } from "../components/StatusBadge";
import { useToast } from "../components/Toast";
import { useAsync } from "../hooks/useAsync";
import { formatDate, maskValue, relationshipLabel } from "../lib/format";
import { api } from "../services/api";
import { ApiError, type ReviewStatus } from "../types/api";

export function InvestigationDetailPage() {
  const { adId = "" } = useParams();
  const toast = useToast();
  const { data, error, loading, reload, setData } = useAsync(() => api.ad(adId), [adId]);
  const [note, setNote] = useState("");

  async function saveReview(review_status: ReviewStatus) {
    try {
      setData(await api.updateReview(adId, review_status));
      toast("Review status saved.");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Could not update review.", "err");
    }
  }

  async function saveNote(event: FormEvent) {
    event.preventDefault();
    if (!note.trim()) return;
    try {
      await api.addNote(adId, note.trim());
      setNote("");
      await reload();
      toast("Analyst note stored.");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Could not save note.", "err");
    }
  }

  if (loading) return <Skeleton className="h-96" />;
  if (error) return <ErrorBanner message={error} onRetry={reload} />;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-mute">Investigation</p>
          <h1 className="mt-1 text-2xl font-semibold">Advertisement detail</h1>
          <p className="mt-1 text-xs text-mute">
            {data.is_seed ? "Synthetic demonstration record." : "Investigator submission."} Score is a rules-based triage indicator, not a probability.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge value={data.risk_category} />
          <span className="text-3xl font-semibold">{data.risk_score}</span>
        </div>
      </div>
      {data.missing_data_warnings && data.missing_data_warnings.length > 0 ? (
        <div className="rounded border border-amber-500/40 bg-amber-500/10 p-3 text-xs text-amber-200">
          <p className="font-semibold">Missing data notice:</p>
          <ul className="mt-1 list-disc pl-4 space-y-1">
            {data.missing_data_warnings.map((warn, i) => (
              <li key={i}>{warn}</li>
            ))}
          </ul>
        </div>
      ) : null}
      <section className="rounded-lg border border-line bg-panel p-5">
        <h2 className="text-sm font-medium">Submitted copy</h2>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed">{data.text || "No text submitted."}</p>
        {data.image_filename ? (
          <img
            src={`/uploads/${data.image_filename}`}
            alt="Uploaded advertisement"
            className="mt-4 max-h-64 rounded border border-line"
          />
        ) : null}
        {data.ocr_status !== "not_requested" ? (
          <p className="mt-3 text-xs text-mute">OCR status: {data.ocr_status}{data.ocr_text ? ` · ${data.ocr_text}` : ""}</p>
        ) : null}
      </section>
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-lg border border-line bg-panel p-5">
          <h2 className="text-sm font-medium">Risk indicators</h2>
          <ul className="mt-3 space-y-3">
            {data.signals.map((signal) => (
              <li key={signal.id} className="border-b border-line pb-3 last:border-0">
                <p className="text-sm font-medium">
                  {signal.title} <span className="text-mute">(+{signal.contribution})</span>
                </p>
                <p className="mt-1 text-sm text-mute">{signal.explanation}</p>
                <p className="mt-1 font-mono text-[11px] text-accent/90">{signal.evidence}</p>
                {signal.recommendation ? (
                  <p className="mt-1.5 text-xs text-emerald-400 font-medium">
                    Verification: {signal.recommendation}
                  </p>
                ) : null}
              </li>
            ))}
            {data.signals.length === 0 ? <p className="text-sm text-mute">No elevated rule-based indicators detected.</p> : null}
          </ul>
          <p className="mt-4 text-xs text-mute">{data.limitations}</p>
          <p className="mt-2 text-sm">{data.recommendation}</p>
        </section>
        <section className="rounded-lg border border-line bg-panel p-5">
          <h2 className="text-sm font-medium">Extracted entities</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {data.entities.filter((e) => e.entity_type !== "phrase").map((entity) => (
              <li key={entity.id} className="rounded border border-line px-3 py-2">
                <span className="text-mute font-mono text-xs uppercase">{entity.entity_type}</span>{" "}
                {maskValue(entity.entity_type, entity.normalized_value)}
                <p className="mt-1 text-[11px] text-mute">{entity.source_text}</p>
              </li>
            ))}
            {data.entities.filter((e) => e.entity_type !== "phrase").length === 0 ? (
              <p className="text-sm text-mute">No contact, payment, or domain identifiers detected.</p>
            ) : null}
          </ul>
        </section>
      </div>
      <section className="rounded-lg border border-line bg-panel p-5">
        <h2 className="text-sm font-medium">
          Content anomalies ({data.anomalies ? data.anomalies.length : 0})
        </h2>
        {data.anomalies && data.anomalies.length > 0 ? (
          <ul className="mt-3 space-y-2">
            {data.anomalies.map((anomaly) => (
              <li key={anomaly.id} className="rounded border border-line p-3 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium text-rose-400">{anomaly.title}</p>
                  <span className="rounded bg-rose-500/10 px-2 py-0.5 text-[10px] font-semibold text-rose-400">
                    {anomaly.severity}
                  </span>
                </div>
                <p className="mt-1 text-xs text-mute">{anomaly.explanation}</p>
                <p className="mt-1 font-mono text-[11px] text-accent/90">Evidence: {anomaly.evidence}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-mute">
            No content anomalies detected. Advertisement claims do not exhibit extreme return outliers, contradictory statements, or institutional mismatches.
          </p>
        )}
      </section>
      <section className="rounded-lg border border-line bg-panel p-5">
        <h2 className="text-sm font-medium">Related advertisements</h2>
        {data.relationships.length === 0 ? (
          <p className="mt-3 text-sm text-mute">No stored relationship evidence for this advertisement.</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {data.relationships.map((rel) => {
              const other = rel.source_ad_id === data.id ? rel.target_ad_id : rel.source_ad_id;
              return (
                <li key={rel.id} className="rounded border border-line px-3 py-2 text-sm">
                  <Link className="text-accent" to={`/investigations/${other}`}>
                    Open related advertisement
                  </Link>
                  <p className="mt-1 text-mute">
                    {relationshipLabel(rel.relationship_type)}
                    {rel.similarity_score != null ? ` · similarity ${rel.similarity_score}` : ""} · {rel.explanation}
                  </p>
                </li>
              );
            })}
          </ul>
        )}
        <Link className="mt-4 inline-block text-sm text-accent" to="/campaigns">
          Open campaign graph
        </Link>
      </section>
      <section className="rounded-lg border border-line bg-panel p-5">
        <h2 className="text-sm font-medium">Investigator review</h2>
        <p className="mt-1 text-xs text-mute">Updating review status does not change the computed risk score.</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {(["unreviewed", "under_review", "escalated", "closed"] as ReviewStatus[]).map((status) => (
            <button
              key={status}
              type="button"
              onClick={() => void saveReview(status)}
              className={`rounded border px-3 py-1 text-sm ${
                data.review_status === status ? "border-accent text-accent" : "border-line text-mute"
              }`}
            >
              {status.replace("_", " ")}
            </button>
          ))}
        </div>
        <form onSubmit={saveNote} className="mt-4 space-y-2">
          <textarea
            className="h-24 w-full rounded border border-line bg-ink px-3 py-2 text-sm"
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Add an analyst note"
          />
          <button type="submit" className="rounded bg-accent px-3 py-1.5 text-sm font-medium text-ink">
            Save note
          </button>
        </form>
        <ul className="mt-4 space-y-2 text-sm">
          {data.notes.map((item) => (
            <li key={item.id} className="border-t border-line pt-2">
              <p>{item.content}</p>
              <p className="text-[11px] text-mute">{formatDate(item.created_at)}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
