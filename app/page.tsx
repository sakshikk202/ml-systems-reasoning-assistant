"use client";

import { useEffect, useState } from "react";

type Scenario = {
  id: string;
  slug: string;
  title: string;
  description: string;
};

type DiagnosisBlock = {
  summary?: string;
  checks?: string[];
  causes?: string[];
  actions?: string[];
};

export default function HomePage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);

  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [loadingScenarios, setLoadingScenarios] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoadingScenarios(true);
      try {
        const res = await fetch("/api/scenarios", { cache: "no-store" });
        if (!res.ok) throw new Error(`Failed to load scenarios (${res.status})`);
        const data = await res.json();
        if (!cancelled) setScenarios(Array.isArray(data) ? data : []);
      } catch {
        if (!cancelled) setScenarios([]);
      } finally {
        if (!cancelled) setLoadingScenarios(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function runDiagnosis(inputPrompt: string, scenarioId?: string) {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("/api/diagnose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: inputPrompt,
          scenarioId: scenarioId ?? null,
        }),
      });

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || "Diagnosis failed");
      }

      const data = await res.json();
      setResult(data);
    } catch (e: any) {
      setError(e?.message ?? "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  // Pull diagnosis safely from API response
  const diagnosis: DiagnosisBlock | null =
    result?.diagnosis && typeof result.diagnosis === "object"
      ? result.diagnosis
      : null;

  const summary = diagnosis?.summary ?? "";
  const checks = Array.isArray(diagnosis?.checks) ? diagnosis!.checks! : [];
  const causes = Array.isArray(diagnosis?.causes) ? diagnosis!.causes! : [];
  const actions = Array.isArray(diagnosis?.actions) ? diagnosis!.actions! : [];

  return (
    <main style={{ maxWidth: 900, margin: "0 auto", padding: 24 }}>
      {/* Header */}
      <section style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, marginBottom: 8 }}>
          ML Systems Reasoning Assistant
        </h1>
        <p style={{ opacity: 0.75 }}>
          Diagnose why ML systems fail in production — with checks, causes, and actions.
        </p>
      </section>

      {/* Scenarios */}
      <section style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 18, marginBottom: 12 }}>
          Demo Scenarios (1-click)
        </h2>

        {loadingScenarios ? (
          <p style={{ opacity: 0.6 }}>Loading scenarios…</p>
        ) : scenarios.length === 0 ? (
          <p style={{ opacity: 0.6 }}>
            No scenarios found yet (or API not reachable).
          </p>
        ) : (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            {scenarios.map((s) => (
              <button
                key={s.id}
                onClick={() => {
                  setSelectedScenario(s);
                  const scenarioPrompt = s.description;
                  setPrompt(scenarioPrompt);
                  runDiagnosis(scenarioPrompt, s.id);
                }}
                style={{
                  padding: "10px 14px",
                  borderRadius: 8,
                  border: "1px solid #ccc",
                  background: selectedScenario?.id === s.id ? "#f0f0f0" : "#fff",
                  color: "#000",
                  cursor: "pointer",
                }}
              >
                {s.title}
              </button>
            ))}
          </div>
        )}
      </section>

      {/* Free text */}
      <section style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 18, marginBottom: 12 }}>
          Custom Prompt (optional)
        </h2>

        <textarea
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the ML production issue you are seeing…"
          style={{
            width: "100%",
            padding: 12,
            borderRadius: 8,
            border: "1px solid #ccc",
            fontSize: 14,
            // you already made this dynamic earlier; keep whatever you currently have
            // If you already have the day/night mode logic, keep it.
          }}
        />

        <div style={{ marginTop: 12, display: "flex", gap: 10 }}>
          <button
            disabled={!prompt || loading}
            onClick={() => runDiagnosis(prompt, selectedScenario?.id)}
            style={{
              padding: "10px 16px",
              borderRadius: 8,
              border: "none",
              background: "#000",
              color: "#fff",
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.6 : 1,
            }}
          >
            {loading ? "Running…" : "Run Diagnosis"}
          </button>

          <button
            disabled={loading}
            onClick={() => {
              setSelectedScenario(null);
              setPrompt("");
              setResult(null);
              setError(null);
            }}
            style={{
              padding: "10px 16px",
              borderRadius: 8,
              border: "1px solid #ccc",
              background: "#fff",
              color: "#000",
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.6 : 1,
            }}
          >
            Reset
          </button>
        </div>
      </section>

      {/* Output */}
      <section>
        <h2 style={{ fontSize: 18, marginBottom: 12 }}>
          Diagnosis Output
        </h2>

        {error && <p style={{ color: "red" }}>{error}</p>}

        {!result && !loading && (
          <p style={{ opacity: 0.6 }}>
            Run a scenario to see structured reasoning output here.
          </p>
        )}

        {result && (
          <div
            style={{
              background: "#f7f7f7",
              padding: 16,
              borderRadius: 8,
              fontSize: 13,
              overflowX: "auto",
              color: "#000",
            }}
          >
            {/* Summary */}
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontWeight: 700, marginBottom: 6 }}>Summary</div>
              <div style={{ opacity: 0.9 }}>
                {summary || "No summary returned."}
              </div>
            </div>

            {/* Checks */}
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontWeight: 700, marginBottom: 6 }}>Checks to run</div>
              {checks.length === 0 ? (
                <div style={{ opacity: 0.7 }}>No checks returned.</div>
              ) : (
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {checks.map((c, idx) => (
                    <li key={`check-${idx}`} style={{ marginBottom: 4 }}>
                      {c}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Causes */}
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontWeight: 700, marginBottom: 6 }}>Likely causes</div>
              {causes.length === 0 ? (
                <div style={{ opacity: 0.7 }}>No causes returned.</div>
              ) : (
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {causes.map((c, idx) => (
                    <li key={`cause-${idx}`} style={{ marginBottom: 4 }}>
                      {c}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Actions */}
            <div>
              <div style={{ fontWeight: 700, marginBottom: 6 }}>Recommended actions</div>
              {actions.length === 0 ? (
                <div style={{ opacity: 0.7 }}>No actions returned.</div>
              ) : (
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {actions.map((a, idx) => (
                    <li key={`action-${idx}`} style={{ marginBottom: 4 }}>
                      {a}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </section>
    </main>
  );
}