"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body style={{ padding: 24 }}>
        <h2>App crashed</h2>
        <pre style={{ whiteSpace: "pre-wrap", marginTop: 12 }}>
          {error?.message}
        </pre>
        <button
          onClick={() => reset()}
          style={{ marginTop: 12, padding: "8px 12px" }}
        >
          Reload
        </button>
      </body>
    </html>
  );
}