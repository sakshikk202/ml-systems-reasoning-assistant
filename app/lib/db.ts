// app/lib/db.ts
import postgres from "postgres";

const connectionString = process.env.DATABASE_URL;

if (!connectionString) {
  throw new Error("DATABASE_URL is not set. Add it to .env.local");
}

// Neon typically requires SSL
export const sql = postgres(connectionString, {
  ssl: "require",
});