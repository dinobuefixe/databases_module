import { NextResponse } from "next/server";
import type { Document } from "mongodb";
import { mongoDb } from "@/lib/mongo";

export const dynamic = "force-dynamic";

const DAY_MS = 24 * 60 * 60 * 1000;

async function docsExamined(pipeline: Document[]): Promise<number> {
  const plan = await mongoDb().collection("customers").aggregate(pipeline).explain("executionStats");
  // When the whole pipeline runs in the query engine the stats are at the top;
  // otherwise they are in the first stage, $cursor.
  const stats = plan.executionStats ?? plan.stages[0].$cursor.executionStats;
  return stats.totalDocsExamined;
}

// GET /api/rentals/match-position?start=2026-07-21: rentals per store in the 7 days from start,
// with the $match late and early. Same result, different work.
export async function GET(request: Request) {
  const start = new Date(new URL(request.url).searchParams.get("start") ?? "2026-07-21");
  if (Number.isNaN(start.getTime())) {
    return NextResponse.json({ error: "start must be YYYY-MM-DD" }, { status: 400 });
  }
  const inRange = { $gte: start, $lt: new Date(start.getTime() + 7 * DAY_MS) };
  const perStore = [{ $group: { _id: "$store_id", rentals: { $sum: 1 } } }, { $sort: { _id: 1 } }];

  // Late: every customer is read and unwound, then the rentals outside the range are dropped.
  const late = [{ $unwind: "$recent_rentals" }, { $match: { "recent_rentals.rental_date": inRange } }, ...perStore];
  // Early: first keep only customers with a rental in the range (this $match can use the
  // index on recent_rentals.rental_date), then unwind and filter the rentals as before.
  const early = [
    { $match: { recent_rentals: { $elemMatch: { rental_date: inRange } } } },
    { $unwind: "$recent_rentals" },
    { $match: { "recent_rentals.rental_date": inRange } },
    ...perStore,
  ];

  const customers = mongoDb().collection("customers");
  const run = async (pipeline: Document[]) => ({
    docs_examined: await docsExamined(pipeline),
    result: await customers.aggregate(pipeline).toArray(),
  });
  return NextResponse.json({ match_late: await run(late), match_early: await run(early) });
}
