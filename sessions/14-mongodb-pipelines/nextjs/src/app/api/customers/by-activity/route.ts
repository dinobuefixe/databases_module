import { NextResponse } from "next/server";
import { mongoDb } from "@/lib/mongo";

export const dynamic = "force-dynamic";

// GET /api/customers/by-activity: $bucket groups customers into ranges of total rentals.
// The _id of each bucket is its lower bound: 0 means 0 to 19 rentals.
export async function GET() {
  const rows = await mongoDb()
    .collection("customers")
    .aggregate([
      {
        $bucket: {
          groupBy: "$rentals_total",
          boundaries: [0, 20, 40, 60, 80, 100],
          default: "other", // where values outside the boundaries would go
          output: { customers: { $sum: 1 }, rentals: { $sum: "$rentals_total" } },
        },
      },
    ])
    .toArray();
  return NextResponse.json(rows);
}
