import { NextResponse } from "next/server";
import { neon } from "@neondatabase/serverless";

export async function GET() {
  const sql = neon(process.env.DATABASE_URL!);

  const rows = await sql`
    SELECT id, title, prompt
    FROM scenario_reasoning.scenarios
    ORDER BY created_at DESC
  `;

  return NextResponse.json({ scenarios: rows });
}