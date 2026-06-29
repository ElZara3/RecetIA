export function Loading() {
  return <div className="center muted">Cargando…</div>;
}

export function ErrorBox({ msg, onRetry }: { msg: string; onRetry?: () => void }) {
  return (
    <div className="center">
      <p className="error">{msg}</p>
      {onRetry && (
        <button className="btn" onClick={onRetry}>
          Reintentar
        </button>
      )}
    </div>
  );
}

export function errMsg(e: unknown): string {
  return e instanceof Error ? e.message : "Ocurrió un error inesperado";
}
