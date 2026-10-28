import { NextResponse } from "next/server";
import { mongoDb } from "@/lib/mongo";
import { rentalsPerMonth } from "@/lib/pipelines";

export const dynamic = "force-dynamic";

// GET /api/rentals/per-month: rentals per month from the rentals embedded in customers.
// Only the last 10 per customer are embedded, so this counts recent activity, not every rental.
export async function GET() {
  const rows = await mongoDb()
    .collection("customers")
    .aggregate([...rentalsPerMonth, { $sort: { _id: 1 } }])
    .toArray();
  return NextResponse.json(rows);
}
