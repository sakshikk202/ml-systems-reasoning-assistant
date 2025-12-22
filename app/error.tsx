"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main style={{ padding: 24 }}>
      <h2>Something went wrong</h2>
      <pre style={{ whiteSpace: "pre-wrap", marginTop: 12 }}>
        {error?.message}
      </pre>
      <button
        onClick={() => reset()}
        style={{ marginTop: 12, padding: "8px 12px" }}
      >
        Try again
      </button>
    </main>
  );
}