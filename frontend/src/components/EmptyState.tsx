export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-dashed border-line bg-panel/60 px-6 py-10 text-center">
      <p className="text-sm font-medium text-paper">{title}</p>
      <p className="mt-2 text-sm text-mute">{body}</p>
    </div>
  );
}
