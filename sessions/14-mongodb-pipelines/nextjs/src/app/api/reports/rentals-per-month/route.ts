import { NextResponse } from "next/server";
import { mongoDb } from "@/lib/mongo";
import { rentalsPerMonth } from "@/lib/pipelines";

export const dynamic = "force-dynamic";

// POST /api/reports/rentals-per-month: $merge writes the pipeline result into a collection.
// _id is the month, so a second run replaces the same documents instead of adding new ones:
// running it again changes nothing.
export async function POST() {
  const db = mongoDb();
  // A pipeline ending in $merge returns no documents; toArray() is what runs it.
  await db
    .collection("customers")
    .aggregate([
      ...rentalsPerMonth,
      { $merge: { into: "rentals_per_month", on: "_id", whenMatched: "replace", whenNotMatched: "insert" } },
    ])
    .toArray();
  const [totals] = await db
    .collection("rentals_per_month")
    .aggregate([{ $group: { _id: null, months: { $sum: 1 }, rentals: { $sum: "$rentals" } } }])
    .toArray();
  return NextResponse.json({ collection: "rentals_per_month", months: totals.months, rentals: totals.rentals });
}

// GET /api/reports/rentals-per-month: reading a materialised report is a plain find, no pipeline runs.
export async function GET() {
  const rows = await mongoDb().collection("rentals_per_month").find().sort({ _id: 1 }).toArray();
  return NextResponse.json(rows);
}
