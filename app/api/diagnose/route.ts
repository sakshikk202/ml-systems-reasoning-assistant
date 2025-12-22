import { NextResponse } from "next/server";
import { sql } from "@/app/lib/db";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type DiagnosisPayload = {
  summary?: string;
  checks?: string[];
  causes?: string[];
  actions?: string[];
  evidence?: string[];
};

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const scenarioId: string | null = body?.scenarioId ?? null;
    const prompt: string = body?.prompt ?? "";
    const diagnosisPayload: DiagnosisPayload = body?.diagnosis ?? {};

    if (!prompt || typeof prompt !== "string") {
      return NextResponse.json({ error: "prompt is required" }, { status: 400 });
    }

    // Insert into Neon/Postgres
    const rows = await sql`
      INSERT INTO scenario_reasoning.diagnosis_runs (scenario_id, input, diagnosis)
      VALUES (${scenarioId}, ${prompt}, ${sql.json(diagnosisPayload)})
      RETURNING id, created_at
    `;

    return NextResponse.json({
      ok: true,
      scenarioId,
      input: prompt,
      diagnosis: diagnosisPayload,
      runId: rows?.[0]?.id ?? null,
      createdAt: rows?.[0]?.created_at ?? null,
    });
  } catch (e: any) {
    console.error("POST /api/diagnose error:", e);
    return NextResponse.json(
      { error: "internal error", details: e?.message ?? String(e) },
      { status: 500 }
    );
  }
}