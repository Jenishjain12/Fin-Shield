export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-lg border border-high/40 bg-high/10 px-4 py-3 text-sm text-rose-100">
      <p>{message}</p>
      {onRetry ? (
        <button className="mt-2 text-accent underline" onClick={onRetry} type="button">
          Retry
        </button>
      ) : null}
    </div>
  );
}
