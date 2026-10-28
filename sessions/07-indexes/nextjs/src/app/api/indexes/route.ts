import { NextResponse } from "next/server";
import { listIndexes } from "@/lib/explain";

export const dynamic = "force-dynamic";

// GET /api/indexes: which indexes exist right now, and how big they are.
export async function GET() {
  return NextResponse.json(await listIndexes());
}
