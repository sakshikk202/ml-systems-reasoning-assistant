import { NextResponse } from "next/server";
import { sql } from "@/app/lib/db";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const rows = await sql`
      SELECT id, scenario_id, input, diagnosis, created_at
      FROM scenario_reasoning.diagnosis_runs
      ORDER BY created_at DESC
      LIMIT 50
    `;

    return NextResponse.json({ results: rows });
  } catch (e: any) {
    console.error("GET /api/results error:", e);
    return NextResponse.json(
      { error: "internal error", details: e?.message ?? String(e) },
      { status: 500 }
    );
  }
}