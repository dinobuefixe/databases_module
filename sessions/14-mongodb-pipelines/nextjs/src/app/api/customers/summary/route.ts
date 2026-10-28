import { NextResponse } from "next/server";
import { mongoDb } from "@/lib/mongo";

export const dynamic = "force-dynamic";

// GET /api/customers/summary: $facet runs two sub-pipelines over the same customers
// and returns both results in one document.
export async function GET() {
  const [summary] = await mongoDb()
    .collection("customers")
    .aggregate([
      {
        $facet: {
          per_store: [
            { $group: { _id: "$store_id", customers: { $sum: 1 }, rentals: { $sum: "$rentals_total" } } },
            { $sort: { _id: 1 } },
          ],
          most_active: [
            { $sort: { rentals_total: -1, _id: 1 } },
            { $limit: 3 },
            { $project: { name: 1, store_id: 1, rentals_total: 1 } },
          ],
        },
      },
    ])
    .toArray();
  return NextResponse.json(summary);
}
