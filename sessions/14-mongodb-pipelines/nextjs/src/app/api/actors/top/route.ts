import { NextResponse } from "next/server";
import { mongoDb } from "@/lib/mongo";

export const dynamic = "force-dynamic";

// GET /api/actors/top: the 10 actors with most films. $unwind turns one film with
// N actors into N documents, one per actor, so they can be grouped by actor.
export async function GET() {
  const rows = await mongoDb()
    .collection("films")
    .aggregate([
      { $unwind: "$actors" },
      { $group: { _id: "$actors.actor_id", name: { $first: "$actors.name" }, films: { $sum: 1 } } },
      { $sort: { films: -1, _id: 1 } },
      { $limit: 10 },
    ])
    .toArray();
  return NextResponse.json(rows);
}
