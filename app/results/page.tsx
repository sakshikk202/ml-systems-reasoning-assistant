"use client";

import { useEffect, useState } from "react";

type DiagnosisRun = {
  id: string;
  scenario_id: string | null;
  input: string;
  diagnosis: {
    summary?: string;
    checks?: string[];
    causes?: string[];
    actions?: string[];
    evidence?: string[];
  };
  created_at: string;
};

export default function ResultsPage() {
  const [runs, setRuns] = useState<DiagnosisRun[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch("/api/results", { cache: "no-store" });

        if (!res.ok) {
          const text = await res.text();
          throw new Error(`GET /api/results failed: ${res.status} ${text}`);
        }

        const data = await res.json();
        setRuns(Array.isArray(data?.results) ? data.results : []);
      } catch (e: any) {
        setError(e?.message ?? String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <main style={{ maxWidth: 900, margin: "40px auto", padding: "0 16px" }}>
      <h1 style={{ fontSize: 28, fontWeight: 700 }}>Diagnosis History</h1>

      {loading && <p style={{ marginTop: 10 }}>Loading…</p>}

      {!loading && error && (
        <div style={{ marginTop: 10, color: "#b00020" }}>
          <div style={{ fontWeight: 600 }}>Failed to load results</div>
          <div style={{ marginTop: 6, fontFamily: "monospace", fontSize: 12 }}>
            {error}
          </div>
        </div>
      )}

      {!loading && !error && runs.length === 0 && (
        <p style={{ marginTop: 10 }}>No diagnosis runs yet.</p>
      )}

      {!loading && !error && runs.length > 0 && (
        <div style={{ marginTop: 16, display: "grid", gap: 12 }}>
          {runs.map((r) => (
            <div
              key={r.id}
              style={{
                border: "1px solid #ddd",
                borderRadius: 10,
                padding: 12,
                background: "white",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                <div style={{ fontWeight: 650 }}>
                  {r.diagnosis?.summary ?? "No summary"}
                </div>
                <div style={{ fontSize: 12, color: "#666" }}>
                  {new Date(r.created_at).toLocaleString()}
                </div>
              </div>

              <div style={{ marginTop: 8, color: "#333" }}>
                <div style={{ fontSize: 12, color: "#666" }}>Input</div>
                <div>{r.input}</div>
              </div>

              <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
                <Section title="Checks" items={r.diagnosis?.checks} />
                <Section title="Causes" items={r.diagnosis?.causes} />
                <Section title="Actions" items={r.diagnosis?.actions} />
                <Section title="Evidence" items={r.diagnosis?.evidence} />
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}

function Section({ title, items }: { title: string; items?: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div>
      <div style={{ fontWeight: 650 }}>{title}</div>
      <ul style={{ marginTop: 6 }}>
        {items.map((x, i) => (
          <li key={i}>{x}</li>
        ))}
      </ul>
    </div>
  );
}