import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ErrorBanner } from "../components/ErrorBanner";
import { StatusBadge } from "../components/StatusBadge";
import { useToast } from "../components/Toast";
import { api } from "../services/api";
import { ApiError, type AdvertisementDetail } from "../types/api";

export function AnalyzePage() {
  const toast = useToast();
  const navigate = useNavigate();
  const [text, setText] = useState("");
  const [source, setSource] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AdvertisementDetail | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!text.trim() && !file) {
      setError("Provide advertisement text or an image.");
      return;
    }
    if (file && file.size > 5 * 1024 * 1024) {
      setError("Image must be 5 MB or smaller.");
      return;
    }
    setBusy(true);
    setError(null);
    const form = new FormData();
    form.set("text", text);
    form.set("source", source);
    form.set("source_url", sourceUrl);
    if (file) form.set("image", file);
    try {
      const analysis = await api.analyze(form);
      setResult(analysis);
      toast("Analysis completed and stored.");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Analysis failed.";
      setError(message);
      toast(message, "err");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Analyze advertisement</h1>
        <p className="mt-1 text-sm text-mute">
          Submitted URLs are parsed as text only and are not fetched. Image OCR is used only if a local OCR engine is available.
        </p>
      </div>
      <form onSubmit={onSubmit} className="space-y-4 rounded-lg border border-line bg-panel p-5">
        <label className="block text-sm">
          Advertisement text
          <textarea
            className="mt-2 h-40 w-full rounded border border-line bg-ink px-3 py-2 text-sm outline-none focus:border-accent"
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Paste copy, including claimed returns, contact numbers, payment handles, and URLs."
          />
        </label>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block text-sm">
            Source channel
            <input
              className="mt-2 w-full rounded border border-line bg-ink px-3 py-2 text-sm outline-none focus:border-accent"
              value={source}
              onChange={(event) => setSource(event.target.value)}
              placeholder="social, messaging, website…"
            />
          </label>
          <label className="block text-sm">
            Reference URL (optional, not fetched)
            <input
              className="mt-2 w-full rounded border border-line bg-ink px-3 py-2 text-sm outline-none focus:border-accent"
              value={sourceUrl}
              onChange={(event) => setSourceUrl(event.target.value)}
              placeholder="https://…"
            />
          </label>
        </div>
        <label className="block text-sm">
          Advertisement image
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="mt-2 block w-full text-sm text-mute"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>
        {error ? <ErrorBanner message={error} /> : null}
        <button
          type="submit"
          disabled={busy}
          className="rounded bg-accent px-4 py-2 text-sm font-semibold text-ink disabled:opacity-50"
        >
          {busy ? "Analyzing…" : "Analyze"}
        </button>
      </form>
      {result ? (
        <section className="space-y-5 rounded-lg border border-line bg-panel p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-mute">Configured triage score</p>
              <p className="text-3xl font-semibold">{result.risk_score}</p>
            </div>
            <StatusBadge value={result.risk_category} />
          </div>

          <p className="text-sm text-mute">{result.recommendation}</p>

          {result.missing_data_warnings && result.missing_data_warnings.length > 0 ? (
            <div className="rounded border border-amber-500/40 bg-amber-500/10 p-3 text-xs text-amber-200">
              <p className="font-semibold">Missing data notice:</p>
              <ul className="mt-1 list-disc pl-4 space-y-1">
                {result.missing_data_warnings.map((warn, i) => (
                  <li key={i}>{warn}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {result.ocr_status !== "not_requested" ? (
            <div className="rounded border border-line bg-ink/40 p-3 text-xs">
              <div className="flex items-center gap-2">
                <span className="font-medium text-mute">OCR status:</span>
                <span
                  className={`font-mono font-medium ${
                    result.ocr_status === "extracted"
                      ? "text-emerald-400"
                      : result.ocr_status === "empty" || result.ocr_status === "unavailable"
                      ? "text-amber-400"
                      : "text-rose-400"
                  }`}
                >
                  {result.ocr_status === "extracted" && "Extracted successfully"}
                  {result.ocr_status === "empty" && "Empty (no readable text found in image)"}
                  {result.ocr_status === "unavailable" && "Unavailable (OCR engine not active)"}
                  {result.ocr_status === "failed" && "Failed (image processing error)"}
                  {result.ocr_status === "missing_file" && "Missing file error"}
                </span>
              </div>
              {result.ocr_text ? (
                <p className="mt-2 text-mute">
                  Extracted text: <span className="font-mono text-ink-text">{result.ocr_text}</span>
                </p>
              ) : null}
            </div>
          ) : null}

          {result.limitations ? (
            <p className="text-xs text-mute border-l-2 border-line pl-2">{result.limitations}</p>
          ) : null}

          <div className="grid gap-5 md:grid-cols-2">
            <div>
              <h2 className="text-sm font-medium">Risk indicators ({result.signals.length})</h2>
              <ul className="mt-2 space-y-2">
                {result.signals.map((signal) => (
                  <li key={signal.id} className="rounded border border-line p-3 text-sm">
                    <p className="font-medium">{signal.title} · +{signal.contribution}</p>
                    <p className="mt-1 text-xs text-mute">{signal.explanation}</p>
                    <p className="mt-1 font-mono text-[11px] text-accent/90">Evidence: {signal.evidence}</p>
                    {signal.recommendation ? (
                      <p className="mt-1.5 text-[11px] text-emerald-400/90 font-medium">
                        Verification: {signal.recommendation}
                      </p>
                    ) : null}
                  </li>
                ))}
                {result.signals.length === 0 ? (
                  <li className="rounded border border-line/60 bg-ink/20 p-3 text-xs text-mute">
                    No elevated rule-based indicators detected.
                  </li>
                ) : null}
              </ul>
            </div>

            <div>
              <h2 className="text-sm font-medium">Extracted entities</h2>
              <ul className="mt-2 space-y-2">
                {result.entities.filter((entity) => entity.entity_type !== "phrase").map((entity) => (
                  <li key={entity.id} className="rounded border border-line p-3 text-sm">
                    <span className="text-mute font-mono text-xs uppercase">{entity.entity_type}</span>:{" "}
                    <span className="font-medium">{entity.normalized_value}</span>
                    <p className="mt-0.5 text-[11px] text-mute font-mono">{entity.source_text}</p>
                  </li>
                ))}
                {result.entities.filter((e) => e.entity_type !== "phrase").length === 0 ? (
                  <li className="rounded border border-line/60 bg-ink/20 p-3 text-xs text-mute">
                    No contact, payment, or domain identifiers detected.
                  </li>
                ) : null}
              </ul>
            </div>
          </div>

          <div className="space-y-3 pt-2 border-t border-line">
            <h2 className="text-sm font-medium">
              Content anomalies ({result.anomalies ? result.anomalies.length : 0})
            </h2>
            {result.anomalies && result.anomalies.length > 0 ? (
              <ul className="space-y-2">
                {result.anomalies.map((anomaly) => (
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
              <div className="rounded border border-line/60 bg-ink/20 p-3 text-xs text-mute">
                No content anomalies detected. Stated advertisement claims do not display extreme return outliers, conflicting risk statements, or institutional credential mismatches.
              </div>
            )}
          </div>

          <div className="space-y-3 pt-2 border-t border-line">
            <h2 className="text-sm font-medium">
              Related advertisements in database ({result.relationships ? result.relationships.length : 0})
            </h2>
            {result.relationships && result.relationships.length > 0 ? (
              <ul className="space-y-2">
                {result.relationships.map((rel) => {
                  const other = rel.source_ad_id === result.id ? rel.target_ad_id : rel.source_ad_id;
                  return (
                    <li key={rel.id} className="rounded border border-line p-3 text-sm">
                      <button
                        type="button"
                        className="font-medium text-accent underline hover:opacity-80"
                        onClick={() => navigate(`/investigations/${other}`)}
                      >
                        Connected record: {other.slice(0, 8)}…
                      </button>
                      <p className="mt-1 text-xs text-mute">
                        {rel.relationship_type.replace("_", " ")}
                        {rel.similarity_score != null ? ` · similarity ${rel.similarity_score}` : ""} · {rel.explanation}
                      </p>
                      <p className="mt-1 font-mono text-[11px] text-accent/80">Evidence key: {rel.evidence}</p>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <div className="rounded border border-line/60 bg-ink/20 p-3 text-xs text-mute">
                No cross-advertisement relationships found in the current dataset.
              </div>
            )}
          </div>

          <div className="pt-2">
            <button
              type="button"
              className="text-sm text-accent underline"
              onClick={() => navigate(`/investigations/${result.id}`)}
            >
              Open full investigation workspace →
            </button>
          </div>
        </section>
      ) : null}
    </div>
  );
}
